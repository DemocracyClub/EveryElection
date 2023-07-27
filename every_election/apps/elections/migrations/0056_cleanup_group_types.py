# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

group_type_map = {
    # These mayoral elections all have group_type='organisation', but they should
    # be None to bring them into line with the current convention for mayor/pcc
    "mayor.west-of-england.2017-05-04": None,
    "mayor.cambridgeshire-and-peterborough.2017-05-04": None,
    "mayor.north-tyneside.2017-05-04": None,
    "mayor.hackney.2018-05-03": None,
    "mayor.doncaster.2017-05-04": None,
    "mayor.tees-valley.2017-05-04": None,
    "mayor.greater-manchester-ca.2017-05-04": None,
    "mayor.west-midlands.2017-05-04": None,
    "mayor.liverpool-city-ca.2017-05-04": None,
    # These election groups have group_type='' for some reason
    "nia.1998-06-25": "election",
    "parl.2000-09-21": "election",
    "nia.2003-11-26": "election",
    "nia.2007-03-07": "election",
    "nia.2011-05-05": "election",
    "parl.2011-06-09": "election",
    "parl.2013-03-07": "election",
    "local.2014-05-22": "election",
    "nia.2016-05-05": "election",
    # These organisation groups have group_type='' for some reason
    "local.belfast.2011-05-05": "organisation",
    "local.antrim-and-newtownabbey.2014-05-22": "organisation",
    "local.ards-and-north-down.2014-05-22": "organisation",
    "local.armagh-city-banbridge-and-craigavon.2014-05-22": "organisation",
    "local.belfast.2014-05-22": "organisation",
    "local.causeway-coast-and-glens.2014-05-22": "organisation",
    "local.derry-city-and-strabane.2014-05-22": "organisation",
    "local.fermanagh-and-omagh.2014-05-22": "organisation",
    "local.lisburn-and-castlereagh.2014-05-22": "organisation",
    "local.mid-and-east-antrim.2014-05-22": "organisation",
    "local.mid-ulster.2014-05-22": "organisation",
    "local.newry-mourne-and-down.2014-05-22": "organisation",
}


def fix_bad_group_types(apps, schema_editor):
    for election_id, group_type in group_type_map.items():
        Election = apps.get_model("elections", "Election")
        try:
            e = Election.private_objects.get(election_id=election_id)
            e.group_type = group_type
            e.save()
        except Election.DoesNotExist:
            # don't throw an exception
            # if we're initializing an enpty DB
            pass


class Migration(migrations.Migration):
    dependencies = [("elections", "0055_auto_20181204_0918")]

    operations = [
        migrations.RunPython(fix_bad_group_types, migrations.RunPython.noop)
    ]
