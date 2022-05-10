import collections
import datetime
import pprint
import subprocess
import time

Result = collections.namedtuple("Result", ["ok", "data"], defaults=[False, None])


class ZFSException(Exception):
    def __init__(self, message, data=None):  # pylint:disable=super-init-not-called
        self.message = message
        self.data = data


# def zfscmd():
#     ZFS_LOCATIONS = [
#         "/usr/bin/zfs",
#         "/sbin/zfs",
#     ]
#     for LOC in ZFS_LOCATIONS:
#         if os.path.isfile(LOC):
#             return LOC
#     raise ZFSException("No zfs executable found!")


# ZFS = zfscmd()
ZFS = "/usr/bin/zfs"


def snapshot_list(dataset=None, ssh_host=None):
    def process(line):
        fs = line.split("\t")
        ds, sn = fs[0].split("@")
        return {
            "dataset": ds,
            "snapshot": sn,
            "creation": datetime.datetime.fromtimestamp(int(fs[1])),
            "creation_utc": datetime.datetime.utcfromtimestamp(int(fs[1])),
            "size": int(fs[2]),
        }

    cmd = [ZFS, "list", "-tsnapshot", "-H", "-p", "-o", "name,creation,used"]
    if ssh_host:
        cmd = ["ssh", ssh_host] + cmd
    if dataset:
        cmd += ["-r", dataset]
    cp = subprocess.run(cmd, text=True, capture_output=True)
    if cp.returncode:
        return Result(ok=False, data=cp)
    snapshots = [process(line) for line in cp.stdout.split("\n") if len(line) > 0]
    return Result(ok=True, data=snapshots)


def take_snapshot(dataset, ssh_host=None, name=None, timestamp=False):
    if not name:
        name = "snapshot"
    if timestamp:
        ts = time.time()
        name += "_%sZ_%s" % (
            datetime.datetime.utcfromtimestamp(ts).strftime("%Y%m%d%H%M%S"),
            datetime.datetime.fromtimestamp(ts).strftime("%Y%m%d%H%M%S"),
        )
    cmd = [ZFS, "snapshot", "%s@%s" % (dataset, name)]
    if ssh_host:
        cmd = ["ssh", ssh_host] + cmd
    cp = subprocess.run(cmd, text=True, capture_output=True)
    if cp.returncode:
        return Result(ok=False, data=cp)
    else:
        return Result(ok=True, data=name)


def delete_snapshot(dataset, snapshot_name):
    cmd = [ZFS, "destroy", "%s@%s" % (dataset, snapshot_name)]
    cp = subprocess.run(cmd, text=True, capture_output=True)
    if cp.returncode:
        return Result(ok=False, data=cp)
    else:
        return Result(ok=True)


def dataset_changed(dataset, snapshot=None):
    if not snapshot:
        r = snapshot_list(dataset)
        if not r.ok:
            raise ZFSException(r.data.stderr, r.data)
        snapshots = sorted(
            [snapshot for snapshot in r.data if snapshot["dataset"] == dataset],
            key=lambda snapshot: snapshot["creation"],
        )
        snapshot = snapshots[-1]["snapshot"]
    cmd = [ZFS, "diff", "%s@%s" % (dataset, snapshot), dataset]
    cp = subprocess.run(cmd, text=True, capture_output=True)
    if cp.returncode:  # pylint:disable=no-else-raise
        raise ZFSException(cp.stderr, cp)
    else:
        return cp.stdout != ""


def send_recv(
    send_dataset,
    recv_dataset,
    send_ssh_host=None,
    recv_ssh_host=None,
    ifchanged=False,
    do_not_snapshot_send=False,
    send_recv_char="0",
):
    """
    Do initial zfs send <dataset>@<snapshot> | zfs recv <dataset> as root

    http://asvignesh.in/zfs-send-receive-non-root-account/
    On the sender side, I used these permissions
      sudo zfs allow -u vignesh send,snapshot,hold sql-pool
    And on the receiver side
      sudo zfs allow -u ubuntu compression,mountpoint,create,mount,receive aws-pool

    For some reason, on initial sending, get error
       Filesystem 'hddzfs/backup/calibre' can not be mounted: Operation not permitted
       cannot mount 'hddzfs/backup/calibre': Invalid argument
    But following runs return no error
    """

    def source_take_snapshot():
        # If do_not_snapshot_send then use last snapshot on send
        # Useful in case of sending datasets that are themselves receiving
        # Otherwise the receiving on the sending dataset would fail
        # Because of extraneous snapshots
        if do_not_snapshot_send:
            if not snaps["send"]:
                raise ZFSException("No snapshot on sending end!")
            return snaps["send"][-1]
        else:
            r = take_snapshot(
                send_dataset,
                ssh_host=send_ssh_host,
                name=f"sendrecv{send_recv_char}",
                timestamp=True,
            )
            if not r.ok:
                raise ZFSException(
                    "Could not take snapshot of %s" % send_dataset, r.data
                )
            return r.data

    def find_last_snapshot():
        r_send = snapshot_list(dataset=send_dataset, ssh_host=send_ssh_host)
        if not r_send.ok:
            if "dataset does not exist" in r_send.data.stderr:
                sns_send = []
            else:
                raise ZFSException(
                    "Could not retrieve list of snapshots from sender", r_send.data
                )
        else:
            sns_send = r_send.data
        r_recv = snapshot_list(dataset=recv_dataset, ssh_host=recv_ssh_host)
        if not r_recv.ok:
            if "dataset does not exist" in r_recv.data.stderr:
                sns_recv = []
            else:
                raise ZFSException(
                    "Could not retrieve list of snapshots from receiver", r_recv.data
                )
        else:
            sns_recv = r_recv.data
        sns_send.sort(key=lambda sn: sn["creation"])
        sns_recv.sort(key=lambda sn: sn["creation"])
        sendsns = [sn for sn in sns_send if sn["dataset"] == send_dataset]
        recvsns = [sn for sn in sns_recv if sn["dataset"] == recv_dataset]
        snaps["send"], snaps["recv"] = sendsns, recvsns

        if not sendsns or not recvsns:
            return None
        last_recv = recvsns[-1]["snapshot"]
        if last_recv not in [sn["snapshot"] for sn in sendsns]:
            return None
        return last_recv

    snaps = {"send": [], "recv": []}
    last_sent_snapshot = find_last_snapshot()
    if (
        last_sent_snapshot
        and ifchanged
        and not dataset_changed(send_dataset, last_sent_snapshot)
    ):
        return Result(ok=True, data=None)
    snapshot_name = source_take_snapshot()
    cmd = "%s send %s %s@%s | %s recv -F %s" % (
        ZFS if not send_ssh_host else f"ssh {send_ssh_host} {ZFS}",
        ("-i %s@%s" % (send_dataset, last_sent_snapshot)) if last_sent_snapshot else "",
        send_dataset,
        snapshot_name,
        ZFS if not recv_ssh_host else f"ssh {recv_ssh_host} {ZFS}",
        recv_dataset,
    )
    cp = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if cp.returncode:
        return Result(ok=False, data=cp)
    else:
        return Result(ok=True, data=snapshot_name)


def weedout_snaps(dataset, delete_before_days=None, scenario="standard"):
    def selsns(d1=None, d2=None):
        if not d2:
            d2 = now
        if not d1:
            d1 = sns[-1]["creation_utc"]
        rez = [rec for rec in sns if d1 <= rec["creation_utc"] <= d2]
        return rez

    def keepone(sel):
        for sn in sel[:-1]:
            print("Deleting %s@%s" % (dataset, sn["snapshot"]))
            if not delete_snapshot(dataset, sn["snapshot"]).ok:
                raise Exception("Cannot delete snapshot")

    def process(d1=None, d2=None):
        sel = selsns(d1, d2)
        if len(sel) > 1:
            pprint.pprint(sel)
            keepone(sel)

    def remove_latest_send_recv(sns):
        """
        For each dataset and each send_recv_char, keep latest one
        so that zfs send/recv doesn't get confused
        """
        def key(sn):
            return (sn["dataset"], sn["snapshot"][: len("send_recv") + 1])

        dic = {}
        for sn in sns:
            if sn["snapshot"].startswith("send_recv"):
                dic[key(sn)] = sn["snapshot"]
        return [
            sn for sn in sns if key(sn) not in dic or sn["snapshot"] != dic[key(sn)]
        ]

    SCENARII = {
        "standard": {
            "grace_period": datetime.timedelta(days=2),
            "hourlies": (1, 24 * 7),
            "dailies": (7, 31),
            "weeklies": (4, 52),
            "monthlies": (12, 60),
            "yearlies": (5, 100),
        },
    }
    try:
        SCENARIO = SCENARII[scenario]
    except KeyError:
        # pylint:disable=raise-missing-from
        raise ZFSException("Unknown scenario %s" % scenario)

    r = snapshot_list(dataset)
    if not r.ok:
        raise ZFSException("Could not retrieve list of snapshots", r.data)
    sns = r.data
    if not sns:
        print("No snapshot found")
        return None
    sns.sort(key=lambda sn: sn["creation_utc"])

    # Keep last send_recv snapshot
    sns = remove_latest_send_recv(sns)

    # Keep everything in last 2weeks
    now = datetime.datetime.utcnow() - SCENARIO["grace_period"]
    # keep only one snapshot every hour
    print("Hourlies")
    h1, h2 = SCENARIO["hourlies"]
    for h in range(h1, h2):
        process(
            d2=now - datetime.timedelta(hours=h),
            d1=now - datetime.timedelta(hours=h + 1),
        )
    # keep only one snapshot every day
    print("Dailies")
    d1, d2 = SCENARIO["dailies"]
    for d in range(d1, d2):
        process(
            d2=now - datetime.timedelta(days=d), d1=now - datetime.timedelta(days=d + 1)
        )
    #
    print("Weeklies")
    w1, w2 = SCENARIO["weeklies"]
    for w in range(w1, w2):
        process(
            d2=now - datetime.timedelta(weeks=w),
            d1=now - datetime.timedelta(weeks=w + 1),
        )
    # keep only one snapshot every month
    print("Monthlies")
    m1, m2 = SCENARIO["monthlies"]
    for m in range(m1, m2):
        process(
            d2=now - datetime.timedelta(weeks=4 * m),
            d1=now - datetime.timedelta(weeks=4 * (m + 1)),
        )
    # keep only one snapshot every year
    print("Yearlies")
    y1, y2 = SCENARIO["yearlies"]
    for y in range(y1, y2):
        process(
            d2=now - datetime.timedelta(days=int(365.25 * y)),
            d1=now - datetime.timedelta(weeks=int(365.25 * (y + 1))),
        )

    if delete_before_days:
        print("Too old")
        limit = now - datetime.timedelta(days=delete_before_days)
        for sn in sns:
            if sn["creation_utc"] < limit:
                print("Deleting %s@%s" % (dataset, sn["snapshot"]))
                if not delete_snapshot(dataset, sn["snapshot"]).ok:
                    raise Exception("Cannot delete snapshot")
