import logging

from proj_log import EnhancedRotatingFileHandler                        

logging.ctmhandler = EnhancedRotatingFileHandler                        
                 
logging.config.fileConfig("proj_log.conf")                              
                            
logger = logging.getLogger("cmsdmock")
logger.error("seerfff")