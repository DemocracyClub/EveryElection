Overview
*********

This library encapsulates timetable legislation for elections run in the United Kingdom and its devolved administrations.

.. code-block:: python

    from sopn_publish_date import StatementPublishDate
    from datetime import date

    publish_date = StatementPublishDate()

    print(publish_date.national_assembly_for_wales(date(2016, 5, 5)))

    # datetime.date(2016, 4, 7)

What is a Statement of Persons Nominated?
------------------------------------------

When an election is called in the United Kingdom, the voting public must have access to the list of candidates who have been nominated to that post.

These documents are called Statements of Persons Nominated, and must be published a set number of working days ahead of the actual election date. The number varies based on:

 * *Type of Post* - Parliamentary, Local, devolved Government, etc.
 * *Country* - The United Kingdom has up to four different rules for the same type of election, one for each country.
 * *Calendar* - each country has their own unique set of Bank Holidays.

