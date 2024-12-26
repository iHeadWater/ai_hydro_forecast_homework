from hydroevaluate.dataloader.common import GPM, GFS, SMAP
from hydroevaluate.dataloader.data_sets import (
    Seq2SeqDatasetForEval,
    SeqForecastDatasetForEval,
)

dataloader_dict = {"gpm": GPM, "gfs": GFS, "smap": SMAP}

dataset_dict = {
    "Seq2SeqDatasetForEval": Seq2SeqDatasetForEval,
    "SeqForecastDatasetForEval": SeqForecastDatasetForEval,
}
