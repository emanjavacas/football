
import pymongo
import csv

from squawka_match import SquawkaMatch


def _mongo_export_xGs(output='xGs.csv'):
    client = pymongo.MongoClient()
    with open(output, 'w') as f:
        header = None
        writer = csv.writer(f)
        for doc in client.squawka.squawka.find():
            try:
                m = SquawkaMatch(doc['data'], path=doc['url'])
                for bg, seq, feats in m.xGs():
                    row = {'seq': seq, **bg, **feats}
                    if header is None:
                        header = list(row.keys())
                        writer.writerow(header)
                    writer.writerow([row[k] for k in header])
            except Exception as e:
                print("Couldn't parse file: {}".format(doc['url']))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='xGs.csv')
    args = parser.parse_args()

    _mongo_export_xGs(output=args.output)
