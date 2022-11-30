import os
import logging
import time

from libcloud.storage.types import Provider
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ObjectDoesNotExistError, ContainerDoesNotExistError

from .hearostorage import HearoStorage


logger = logging.getLogger("tartar.infared.hearocloudfiles")


class HearoCloudFiles(HearoStorage):
    """ Abstractd Library For CloudFiles """

    def conn(self):
        """ connects to cloudfiles
            returns the connection
        """
        c = self.context.getService("cloudfiles")

        username = os.getenv("CLOUDFILES_USERNAME", c["username"])
        password = os.getenv("CLOUDFILES_PASSWORD", c["password"])
        region = os.getenv("CLOUDFILES_REGION", c["region"])

        cloudfilesdriver = get_driver(Provider.CLOUDFILES)
        cloudfilesconn = cloudfilesdriver(username, password, region=region)

        logger.debug("connected to cloudfiles %s", str(cloudfilesconn))

        return cloudfilesconn

    def reUpload(self, containeralias, key, path):
        """ uploads a song at location: path to key on container containername """

        for i in range(3):
            try:
                cloudfilesconn = self.conn()
                containername = self.getcontainername(containeralias, "cloudfiles")
                container = cloudfilesconn.get_container(containername)

                logger.debug("objects in container %s", container.extra["object_count"])

                try:
                    obj = container.get_object(key)
                    logger.info("object %s with name %s found", str(obj), key)
                except ObjectDoesNotExistError:
                    logger.info("object %s will be uploaded from path %s", key, path)
                    with open(path, "rb") as iterator:
                        obj = cloudfilesconn.upload_object_via_stream(
                            iterator=iterator, container=container, object_name=key
                        )
                    logger.info("object %s uploaded from path %s", key, path)

                try:
                    return (key, obj.get_cdn_url())
                except ContainerDoesNotExistError as e:
                    return (key, None)

            except Exception as e:
                logger.exception("Error #%s: %s", i, e)
                time.sleep(5)
                continue
        return True

    def download(self, containeralias, key, path):
        """
            will be part of infrared in the future
            maybe?
        """

        for i in range(3):
            try:
                cloudfilesconn = self.conn()
                containername = self.getcontainername(containeralias, "cloudfiles")
                container = cloudfilesconn.get_container(containername)

                logger.debug("objects in container %s", container.extra["object_count"])

                obj = container.get_object(key)

                logger.info("object %s with name %s found", str(obj), key)
                logger.debug("object %s will be downloaded to path %s", key, path)

                obj.download(path)
                logger.info("object %s downloaded to path %s", key, path)

            except Exception as e:
                logger.exception("Error #%s: %s", i, e)
                time.sleep(5)
                continue

        return True

    def delete(self, containeralias, key):
        """ Deletes the file at key in container, container
        """

        try:
            cloudfilesconn = self.conn()
            containername = self.getcontainername(containeralias, "cloudfiles")
            container = cloudfilesconn.get_container(containername)

            logger.info("objects in container %s", container.extra["object_count"])

            obj = container.get_object(key)
            obj.delete_object(key)
        except Exception as e:
            logger.exception(e)
            return False

        return True

    def publicurl(self, containeralias, key):
        """ returns the public url for a key
        """
        cloudfilesconn = self.conn()
        containername = self.getcontainername(containeralias, "cloudfiles")
        container = cloudfilesconn.get_container(containername)
        obj = container.get_object(key)
        return obj.get_cdn_url()

    def exists(self, containeralias, key):
        """ tests if they filename, key, exists in cloudfiles container named containername
        """
        try:
            cloudfilesconn = self.conn()
            containername = self.getcontainername(containeralias, "cloudfiles")
            container = cloudfilesconn.get_container(containername)
            logger.debug("objects in container %s", container.extra["object_count"])

            try:
                obj = container.get_object(key)
                return True
            except ObjectDoesNotExistError:
                return False

        except Exception as e:
            logger.exception(e)
            return False
