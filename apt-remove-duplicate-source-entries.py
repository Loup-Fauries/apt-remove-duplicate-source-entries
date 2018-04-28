#!/usr/bin/python3 -Es
"""
Detects and interactively deactivates duplicate Apt source entries in
`/etc/sources.list' and `/etc/sources.list.d/*.list'.

Source code at https://github.com/davidfoerster/apt-remove-duplicate-source-entries
"""

from __future__ import print_function
from collections import defaultdict
import sys, itertools
from os.path import normpath
from urllib.parse import urlparse, urlunparse


def _get_python_packagename(basename):
	version = sys.version_info.major
	version_part = str(version) if version >= 3 else ''
	return 'python{0:s}-{1:s}'.format(version_part, basename)

try:
	import aptsources.sourceslist
except ImportError as ex:
	print(
		"Erreur: {0!s}.\n\n"
		"Avez vous le paquet '{1:s}' installé ?\n"
		"Sinon vous pouvez le faire comme cela 'sudo apt-get install {1:s}'."
			.format(ex, _get_python_packagename('apt')),
		file=sys.stderr)
	sys.exit(127)


def get_duplicates(sourceslist):
	"""
	Detects and returns duplicate Apt source entries.
	"""

	sentry_map = defaultdict(list)
	for se in sourceslist.list:
		if not se.invalid and not se.disabled:
			uri = urlparse(se.uri)
			uri = urlunparse(uri._replace(path=normpath(uri.path)))
			dist = normpath(se.dist)
			for c in (se.comps or (None,)):
				sentry_map[(se.type, uri, dist, c and normpath(c))].append(se)

	return filter(lambda dupe_set: len(dupe_set) > 1, sentry_map.values())


def _argparse(args):
	import argparse
	parser = argparse.ArgumentParser(**dict(zip(
		('description', 'epilog'), map(str.strip, __doc__.rsplit('\n\n', 1)))))
	parser.add_argument('-y', '--yes',
		dest='apply_changes', action='store_const', const=True,
		help='Applique automatiquement les changements.')
	parser.add_argument('-n', '--no-act', '--dry-run',
		dest='apply_changes', action='store_const', const=False,
		help="N'applique pas les changements; Affiche seulement ce qui peut être fait.")
	return parser.parse_args(args)


def main(*args):
	input = getattr(__builtins__, 'raw_input', __builtins__.input)

	args = _argparse(args or None)
	sourceslist = aptsources.sourceslist.SourcesList(False)
	duplicates = tuple(get_duplicates(sourceslist))

	if duplicates:
		for dupe_set in duplicates:
			orig = dupe_set.pop(0)
			for dupe in dupe_set:
				print(
					'Entrées superposées:\n'
					'  1. {0}: {1}\n'
					'  2. {2}: {3}\n'
					"J'ai désactivé la dernière entrée.".format(
						orig.file, orig, dupe.file, dupe),
					end='\n\n')
				dupe.disabled = True

		print('\n{0} Les entrées suivantes ont été désactivées:'.format(len(duplicates)),
			*itertools.chain(*duplicates), sep='\n  ', end='\n\n')

		if args.apply_changes is None:
			if input('Voulez vous sauvegarder ces changements? (y/N) ').upper() != 'Y':
				return 2
		if args.apply_changes is not False:
			sourceslist.save()

	else:
		print("Aucun doublon n'a été trouvé.")

	return 0


if __name__ == '__main__':
	sys.exit(main())
