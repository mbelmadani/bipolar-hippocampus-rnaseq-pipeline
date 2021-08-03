import gzip
import logging
import os
from os.path import join

from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, DynamicWrapperTask
import luigi
from luigi.util import requires

from .geo import DownloadGeoSample
from .sra import DownloadSraExperiment
from ..utils import gemma_api

logger = logging.getLogger('luigi-interface')

class DownloadGemmaExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Download an experiment described by a Gemma dataset using the REST API.

    Gemma itself does not retain raw data, so this task delegates the work to
    other sources.
    """
    experiment_id = luigi.Parameter()

    def run(self):
        data = gemma_api.samples(self.experiment_id)
        download_sample_tasks = []
        for sample in data:
            accession = sample['accession']['accession']
            external_database = sample['accession']['externalDatabase']['name']
            if external_database == 'GEO':
                download_sample_tasks.append(DownloadGeoSample(accession))
            elif external_database == 'SRA':
                download_sample_tasks.append(DownloadSraExperiment(accession))
            else:
                logger.warning('Downloading %s from %s is not supported.', accession, external_database)
                continue
        yield download_sample_tasks

@requires(DownloadGemmaExperiment)
class ExtractGemmaExperimentBatchInfo(luigi.Task):
    def run(self):
        with self.output().open('w') as info_out:
            for sample in self.requires().requires():
                if not isinstance(sample, DownloadGeoSample):
                    logger.warning('Extracting batch info from %s is not supported.', sample)
                    continue

                if len(sample.output()) == 0:
                    logger.warning('GEO sample %s has no associated FASTQs from which batch information can be extracted.', sample.sample_id)
                    continue

                # TODO: find a cleaner way to obtain the SRA run accession
                for fastq in sample.output():
                    # strip the two extensions (.fastq.gz)
                    fastq_name, _ = os.path.splitext(fastq.path)
                    fastq_name, _ = os.path.splitext(fastq_name)

                    fastq_id = os.path.basename(fastq_name)

                    platform_id, srx_uri = sample_geo_metadata[sample.sample_id]

                    with gzip.open(fastq.path, 'rt') as f:
                        fastq_header = f.readline().rstrip()

                    info_out.write('\t'.join([sample.sample_id, fastq_id, platform_id, srx_uri, fastq_header]) + '\n')

    def output(self):
        return luigi.LocalTarget(join(cfg.output_dir, 'fastq_headers', '{}.fastq-header'.format(self.experiment_id)))
