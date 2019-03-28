sopn-publish-date
************************

This library encapsulates timetable legislation for elections run in the United Kingdom and its devolved administrations.

.. code-block:: python

    from sopn_publish_date import StatementPublishDate
    from datetime import date

    publish_date = StatementPublishDate()

    print(publish_date.national_assembly_for_wales(date(2016, 5, 5)))

    # datetime.date(2016, 4, 7)


.. toctree::
   :maxdepth: 2

   api