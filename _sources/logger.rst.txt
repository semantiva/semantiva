Logger
======

Semantiva uses Python's standard ``logging`` module and exposes a small layer
on top for convenience and trace consistency.

Module
------

.. automodule:: semantiva.logger.logger
   :members:
   :undoc-members:

From the CLI
------------

Verbosity flags map to logging levels:

- ``-q`` → WARNING
- ``-v`` → INFO
- ``-vv`` → DEBUG

When running via :command:`semantiva run` or :command:`semantiva inspect` these
flags control both console output and, where configured, file logging.

Advanced configuration
----------------------

You can customise logging using standard logging configuration mechanisms
(for example ``logging.config.dictConfig`` or file-based configs) as long as
they respect:

- The logger names used in Semantiva (such as ``semantiva`` and
  ``semantiva.trace``).
- The fact that trace drivers may emit structured records independently of
  logging.

In distributed settings (for example when using ``semantiva-ray``) log file
naming and log shipping are handled by the integration layer. See the
corresponding extension documentation for details.
