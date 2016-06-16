#!/usr/bin/env python
# -*- coding:utf-8 -*-

# description:log util func

import logging
import logging.config
import logging.handlers
import os
import time
import sys

from constant import proj_log_conf_path
from ini_parse import IniParse


class TimeAndSizeRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    def __init__(self, filename, when='h', interval=1, backupCount=0, maxBytes=0, encoding=None, delay=0, utc=0):
        """ This is just a combination of TimedRotatingFileHandler and RotatingFileHandler (adds maxBytes to TimedRotatingFileHandler)  """
        logging.handlers.TimedRotatingFileHandler.__init__(self, filename, when, interval, backupCount, encoding, delay, utc)
        self.maxBytes = maxBytes

    @staticmethod
    def rename_file_win(src_path, dst_path):
        with open(src_path, "r") as fp:
            content = fp.read()

        with open(dst_path, "w") as fp:
            fp.write(content)

    @staticmethod
    def enhanced_rename(src_path, dst_path):
        if sys.platform == "win32":
            TimeAndSizeRotatingFileHandler.rename_file_win(src_path, dst_path)
        else:
            os.rename(src_path, dst_path)

    def _open(self):
        prevumask = os.umask(000)
        baseDir = os.path.dirname(self.baseFilename)
        if not os.path.exists(baseDir):
            os.makedirs(baseDir)
        rtv = logging.handlers.TimedRotatingFileHandler._open(self)
        os.umask(prevumask)
        return rtv

    def shouldRollover(self, record):
        """
        Determine if rollover should occur.

        Basically, see if the supplied record would cause the file to exceed
        the size limit we have.

        we are also comparing times        
        """
        if self.stream is None:                 # delay was set...
            self.stream = self._open()
        if self.maxBytes > 0:                   # are we rolling over?
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)  #due to non-posix-compliant Windows feature
            # print "321", self.stream.tell() + len(msg), self.maxBytes
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return 1
        t = int(time.time())
        if t >= self.rolloverAt:
            return 1
        # print "No need to rollover: %d, %d" % (t, self.rolloverAt)
        return 0         

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
        # get the time that this sequence started at and make it a TimeTuple
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        if self.backupCount > 0:
            cnt = 1
            dfn2 = "%s.%03d" % (dfn, cnt)
            while os.path.exists(dfn2):
                dfn2 = "%s.%03d" % (dfn,cnt)
                cnt += 1
            TimeAndSizeRotatingFileHandler.enhanced_rename(self.baseFilename, dfn2)
            # os.rename(self.baseFilename, dfn2)
            for s in self.getFilesToDelete():
                os.remove(s)
        else:
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
        # print "%s -> %s" % (self.baseFilename, dfn)
        self.mode = 'w'
        self.stream = self._open()
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        prefix = baseName + "."
        plen = len(prefix)


        for fileName in fileNames:
            if fileName[:plen] == prefix:
                suffix = fileName[plen:-4]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

logging.handlers.TimeAndSizeRotatingFileHandler = TimeAndSizeRotatingFileHandler
logging.config.fileConfig(proj_log_conf_path)

get_logger = lambda name: logging.getLogger(name)

proj_conf_obj = IniParse(proj_log_conf_path)
proj_logger_handler_value = proj_conf_obj.get("handlers", "keys")
proj_logger_handler_list = proj_logger_handler_value.split(",")

proj_logger_dict = {each: get_logger(each)
                    for each in proj_logger_handler_list}
