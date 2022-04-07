import concurrent.futures
from exportutils import *
import time

exporter = ELKImporter()
nessus = Nessus(exporter.nessus_access_key, exporter.nessus_secret_key, exporter.nessus_url)
elk = ELK(exporter.elk_url, exporter.elk_auth)


def process_scan(scan):
    nessus_lmd = nessus.last_modification_date(scan["id"])
    exporter_lmd = exporter.get_index_history(scan["name"])
    if scan["name"] not in exporter.get_indexes():
        exporter.add_index(scan['name'], nessus_lmd)
        created, existed, benchmark = exporter.export_scan(nessus, elk, scan)
        print(f"{scan['name']}: Created: {created}. Unchanged: {existed}. Time: {benchmark}")
    elif (scan["name"] in exporter.get_indexes()) and (nessus_lmd != exporter_lmd):
        exporter.update_history(scan['name'], nessus_lmd)
        created, existed, benchmark = exporter.export_scan(nessus, elk, scan)
        print(f"{scan['name']}: Created: {created}. Unchanged: {existed}. Time: {benchmark}")
    else:
        print(f"{scan['name']} has no updates.")


if __name__ == "__main__":
    while True:
        t1 = time.time()
        # single thread:
        # for scan in nessus.get_scans():
        #     process_scan(scan)
        #     break
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(process_scan, nessus.get_scans())

        print(f"Total Time: {time.time() - t1}. Sleeping for {exporter.polling_interval} seconds.")
        time.sleep(exporter.polling_interval)
