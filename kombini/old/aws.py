import gzip
import hashlib
import json
import os.path
import shutil

from contextlib import closing
from tempfile import gettempdir

from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError

import outils.logger


def hashit(obj):
    objs = json.dumps(obj).encode("utf-8")
    m = hashlib.sha3_256(objs)
    return m.hexdigest()


LOCAL_BUCKET = os.path.expanduser("~/tmp/polly_bucket")
POLLY_TMP_FILE = os.path.expanduser("~/tmp/polly.mp3")


def _ensure_ptdf():
    dn = os.path.dirname(POLLY_TMP_FILE)
    if not os.path.isdir(dn):
        os.makedirs(dn)


_ensure_ptdf()


class Polly:
    def __init__(
        self,
        profile_name="chunglak",
        s3_bucket="chunglak.eibot.polly",
        local_bucket=LOCAL_BUCKET,
        logger=None,
    ):
        self.logger = outils.logger.default_logger(logger)
        self.profile_name = profile_name
        self.s3_bucket = s3_bucket
        self.local_bucket = local_bucket
        if not os.path.isdir(local_bucket):
            os.makedirs(local_bucket)

        # Lazy loading
        self._session = None
        self._polly = None
        self._s3_client = None

    @property
    def session(self):
        if self._session is None:
            self._session = Session(profile_name=self.profile_name)
        return self._session

    @property
    def polly(self):
        if self._polly is None:
            self._polly = self.session.client("polly")
        return self._polly

    @property
    def s3_client(self):
        # Create a client using the credentials and region defined in the [adminuser]
        # section of the AWS credentials file (~/.aws/credentials).
        if self._s3_client is None:
            self._s3_client = self.session.client("s3")
        return self._s3_client

    def text_to_speech(self, text, voice_id, file_name=None):
        def mk_desc():
            desc_file_name = object_name + ".json.gz"
            desc_path = os.path.join(gettempdir(), desc_file_name)
            gzip.open(desc_path, "wb").write(json.dumps(key).encode("utf-8"))
            return (desc_file_name, desc_path)

        key = (text.strip().lower(), voice_id)
        object_name = hashit(key) + ".mp3"
        local_path = os.path.join(self.local_bucket, object_name)
        if not file_name:
            file_name = POLLY_TMP_FILE

        # Search locally
        if object_name in os.listdir(self.local_bucket):
            shutil.copyfile(local_path, file_name)
            self.logger.info("Found text locally")
            return file_name

        desc_file_name, desc_path = mk_desc()
        local_desc_path = os.path.join(self.local_bucket, desc_file_name)

        # Search remotely
        try:
            self.s3_client.download_file(self.s3_bucket, object_name, file_name)
            self.logger.info("Found text in S3")
            shutil.copyfile(file_name, local_path)
            shutil.copyfile(desc_path, local_desc_path)
            return file_name
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code != "404":
                self.logger.error(e)
                return None

        # Synthesize
        try:
            # Request speech synthesis
            response = self.polly.synthesize_speech(
                Engine="standard",
                OutputFormat="mp3",
                # OutputFormat="ogg_vorbis",
                Text=text,
                VoiceId=voice_id,
            )
        except (BotoCoreError, ClientError) as error:
            # The service returned an error, exit gracefully
            self.logger.error(error)
            return None
        # Access the audio stream from the response
        if "AudioStream" in response:
            # Note: Closing the stream is important because the service throttles on the
            # number of parallel connections. Here we are using contextlib.closing to
            # ensure the close method of the stream object will be called automatically
            # at the end of the with statement's scope.
            with closing(response["AudioStream"]) as stream:
                try:
                    # Open a file for writing the output as a binary stream
                    with open(file_name, "wb") as fh:
                        fh.write(stream.read())
                    self.logger.info("Synthesized from Polly")
                except IOError as error:
                    # Could not write to file, exit gracefully
                    self.logger.error(error)
                    return None
        else:
            # The response didn't contain audio data, exit gracefully
            self.logger.error("Could not stream audio")
            return None

        # Save locally
        shutil.copyfile(desc_path, local_desc_path)
        shutil.copyfile(file_name, local_path)
        self.logger.info("Saved locally")

        # Save to S3
        try:
            resp = self.s3_client.upload_file(desc_path, self.s3_bucket, desc_file_name)
            resp = self.s3_client.upload_file(file_name, self.s3_bucket, object_name)
            self.logger.info("Saved to S3")
        except ClientError as error:
            self.logger.error(error)
            return None

        return file_name
