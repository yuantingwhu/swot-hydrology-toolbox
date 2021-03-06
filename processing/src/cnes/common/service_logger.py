#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id:
#
# ======================================================
#
# Project : SWOT
# Program : common python modules
# Produit par Capgemini.
#
# ======================================================
# HISTORIQUE
#
# FIN-HISTORIQUE
# ======================================================
'''
 This file is part of the SWOT Hydrology Toolbox
 Copyright (C) 2018 Centre National d’Etudes Spatiales
 This software is released under open source license LGPL v.3 and is distributed WITHOUT ANY WARRANTY, read LICENSE.txt for further details.
'''



"""
.. module:: service_logger.py
    :synopsis: logging class for Swot

"""

import sys
import logging
import logging.handlers
import cnes.common.service_config_file as service_config_file

# pointer to the module object instance itself.
THIS = sys.modules[__name__]

THIS.klass = None

# Used in unitary test
def get_instance():
    """
        This function return the instance of the class
        ServiceLogger
    """
    return THIS.klass

class ServiceLogger(logging.getLoggerClass()):
    """
        The class ServiceLogger defines all logging parameter.
        It's an interface to python logging class.
        It's define as a singleton
    """
    instance = None
    def __new__(cls):
        if cls.instance is None:
            cls.instance = object.__new__(cls)
        return cls.instance

    def __init__(self):
        """
            Init class ServiceLogger
            :param name: name of the logger
        """
        THIS.klass = self
        cfg = service_config_file.get_instance()
        # logging format
        # LEVEL : DEBUG, INFO, WARNING, ERROR
        # log format :
        # YYYY-MM-DDThh:mm:ss.mmm     LEVEL:ClassName:FunctionName: message
        self.log_formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d     %(levelname)s | %(name)s::%(funcName)s | %(message)s',
                                               datefmt='%Y-%m-%dT%H:%M:%S')

        # set the name of the class in log messages
        self.root_logger = logging.getLogger()
        # set the logging level from the configuration file
        self.root_logger.setLevel(cfg.get('LOGGING', 'logFileLevel'))
        if not hasattr(self, 'first'):
            # First call to ServiceLogger
            self.first = True
            # create a log file
            self.file_handler = logging.FileHandler(cfg.get('LOGGING', 'logFile'), mode='w')
            self.file_handler.setFormatter(self.log_formatter)
            self.file_handler.setLevel(cfg.get('LOGGING', 'logFileLevel'))
            # create a memory Handler to bufferize SAS log message
            self.memory_handler = logging.handlers.MemoryHandler(1000, target=self.file_handler)
            # add logger
            self.root_logger.addHandler(self.memory_handler)

            if cfg.get('LOGGING', 'logConsole') == 'True':
                # logging in console
                self.console_handler = logging.StreamHandler()
                self.console_handler.setFormatter(self.log_formatter)
                self.console_handler.setLevel(cfg.get('LOGGING', 'logConsoleLevel'))
                self.root_logger.addHandler(self.console_handler)
            else:
                self.console_handler = None
                    

    def flush_log(self):
        """
            This method flush the log file
        """
        self.memory_handler.flush()

    def close(self):
        """
            This method close the logging file
        """
        self.memory_handler.close()
        self.root_logger.removeHandler(self.memory_handler)
        self.file_handler.close()
        self.root_logger.removeHandler(self.file_handler)
        if self.console_handler is not None:
            self.console_handler.close()
            self.root_logger.removeHandler(self.console_handler)
        del self.first
        self.instance = None
        THIS.klass = None
####################################################################
####################################################################


