from rnaseq_pipeline.utils import *

def test_parse_illumina_fastq_header():
    # 1.4 flavour
    fastq_header = IlluminaFastqHeader.parse('HS32_14737:1:2104:16434:41647')
    assert fastq_header.flowcell_lane == '1'
    assert fastq_header.get_batch_factor() == ('HS32_14737', '1')

    # make sure that we can combine it with a GEO platform id
    assert ('GPL1111',) + fastq_header.get_batch_factor() == ('GPL1111', 'HS32_14737', '1')

    # 1.8 flavour
    fastq_header = IlluminaFastqHeader.parse('NIRVANA:127:C08GPACXX:4:1101:1487:2137')
    assert fastq_header.device == 'NIRVANA'
    assert fastq_header.get_batch_factor() == ('NIRVANA', 'C08GPACXX', '4')

    # make sure that we can combine it with a GEO platform id
    assert ('GPL1111',) + fastq_header.get_batch_factor() == ('GPL1111', 'NIRVANA', 'C08GPACXX', '4')