import torch
from torch.utils.data import Dataset
from torch.nn.utils.rnn import pad_sequence
import re

def ids_to_tokens(ids_list, vocabulary):
    # Create a reverse vocabulary, mapping id -> token
    reverse_vocab = {id: token for token, id in vocabulary.items()}

    return [reverse_vocab[id] for id in ids_list]

def BPE_to_eval(BPE_list):

    sentence = ' '.join(BPE_list)
    replace_string = re.sub(r'(@@ )|(@@ ?$)', '', sentence)

    return replace_string

def epoch_time(start_time, end_time):
    elapsed_time = end_time - start_time
    elapsed_mins = int(elapsed_time / 60)
    elapsed_secs = int(elapsed_time - (elapsed_mins * 60))
    return elapsed_mins, elapsed_secs


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

class TextSamplerDataset(Dataset):
    def __init__(self, X, Y, max_len):
        # Get source and target texts
        self.src = X
        self.tgt = Y

        # Get the max_len
        self.max_len = max_len

    def __len__(self):
        return len(self.src)

    '''
    __getitem__ runs on 1 example at a time. Here, we get an example at index and return its numericalize source and
    target values using the vocabulary objects we created in __init__
    '''

    def __getitem__(self, index):
        src = self.src[index]
        src = src[:self.max_len]
        tgt = self.tgt[index]
        tgt = tgt[:self.max_len]
        return torch.IntTensor(src), torch.IntTensor(tgt)


class MyCollate:
    def __init__(self, pad_idx):
        self.pad_idx = pad_idx

    def __call__(self, batch):
        # get all source indexed sentences of the batch
        source = [item[0] for item in batch]
        # pad them using pad_sequence method from pytorch.
        source = pad_sequence(source, batch_first=True, padding_value=self.pad_idx)

        # get all target indexed sentences of the batch
        target = [item[1] for item in batch]
        # pad them using pad_sequence method from pytorch.
        target = pad_sequence(target, batch_first=True, padding_value=self.pad_idx)
        return source, target


def mpp_generate_postprocessing(tensor_ids, eos_token):
    list_ids = tensor_ids.tolist()[0]

    try:
        target_index = list_ids.index(eos_token) + 1
    except ValueError:
        target_index = None

    return tensor_ids[0][:target_index].unsqueeze(0)