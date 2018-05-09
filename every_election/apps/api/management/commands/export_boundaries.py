import os
import os.path
import subprocess
from datetime import datetime, timedelta

import geojson

from django.conf import settings
from django.core.management.base import BaseCommand
from elections.models import Election


def set_precision(coords, precision):
    result = []
    try:
        return round(coords, int(precision))
    except TypeError:
        for coord in coords:
            result.append(set_precision(coord, precision))
    return result


def parse_date(date_string):
    return datetime.strptime(date_string, '%Y-%m-%d').date()


class Command(BaseCommand):
    help = 'Export static boundary GeoJSON files for each group of elections.'

    def add_arguments(self, parser):
        output_dir = os.path.join(settings.BASE_DIR, 'static', 'exports')
        parser.add_argument('--from', dest='from',
                            help='Export elections from this date',
                            type=parse_date,
                            default=datetime.now().date())
        parser.add_argument('--to', dest='to',
                            help='Export elections until this date',
                            type=parse_date,
                            default=(datetime.now() + timedelta(days=180)).date())
        parser.add_argument('--output', dest='output',
                            help='Output directory (default every_election/static/exports)',
                            default=output_dir)

    def handle(self, *args, **options):
        try:
            os.mkdir(options['output'])
        except FileExistsError:
            pass

        elections = Election.objects.all().filter(group_type='election')\
            .filter(poll_open_date__gte=options['from'])\
            .filter(poll_open_date__lte=options['to'])

        for election in elections:
            self.stdout.write("Exporting elections for group %s" % election)
            data = self.export_election(election)

            gj_path = os.path.join(options['output'], '%s.json' % election.election_id)
            with open(gj_path, 'w') as output_file:
                geojson.dump(data, output_file)

            tj_path = os.path.join(options['output'], '%s-topo.json' % election.election_id)
            self.topojson_convert(gj_path, tj_path)
            tj_simple_path = os.path.join(options['output'], '%s-topo-simplified.json' % election.election_id)
            self.topojson_simplify(tj_path, tj_simple_path)

    def topojson_convert(self, source, dest):
        " Convert GeoJSON to TopoJSON by calling out to the topojson package "
        subprocess.check_call(['geo2topo', '-o', dest, source])

    def topojson_simplify(self, source, dest):
        " Simplify a TopoJSON file "
        # The toposimplify settings here were arrived at by trial and error to keep the
        # simplified 2018-05-03 local elections topojson below 2.5MB.
        subprocess.check_call(['toposimplify', '-S', '0.2', '-F', '-o', dest, source])

    def export_election(self, parent):
        " Return GeoJSON containing all leaf elections below this parent "
        features = []
        elections = self.get_leaf_elections(parent)
        for election in elections:
            if not election.geography:
                self.stderr.write("Election %s has no geography" % election)
                continue

            gj = geojson.loads(election.geography.geography.json)

            # Round coordinates to 6 decimal places (~10cm) precision to reduce
            # output size. This is probably as good as the source data accuracy.
            gj['coordinates'] = set_precision(gj['coordinates'], 6)

            feat = geojson.Feature(geometry=gj,
                                   id=election.election_id,
                                   properties={
                                        'name': election.election_title,
                                        'division': election.division.name,
                                        'organisation': election.organisation.official_name
                                   })
            features.append(feat)
        return geojson.FeatureCollection(features,
                                         election_group=parent.election_id)

    def get_leaf_elections(self, group):
        " Return the leaf-level elections for a group. "
        to_visit = [group]
        leaf_nodes = []
        while len(to_visit) > 0:
            e = to_visit.pop()
            children = e.children.all()
            if len(children) == 0:
                leaf_nodes.append(e)
            else:
                to_visit += children

        return leaf_nodes
