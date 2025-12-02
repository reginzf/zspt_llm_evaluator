import os

os.environ['HF_ENDPOINT'] = 'https://hub.gitcode.com'
from datasets import load_dataset,Column

DATA_SET = "hf_mirrors-google/xtreme"


class XtremeDataset:
    def __init__(self, language):
        self.language = language
        self.dataset = load_dataset(DATA_SET, language)

    def run_comprehensive_test(self):
        i = 10
        while i > 0:
            for key, value in self.dataset.items():
                print(f'key: {key}')
                for ele in value["context"]:
                    print(ele)
            i-=1

if __name__ == '__main__':
    XtremeDataset("MLQA.de.zh").run_comprehensive_test()
