import gzip
import numpy as np
import tqdm
import json
import time

from torch import optim
from transformers.optimization import get_constant_schedule_with_warmup
from model.optimizer import get_optimizer

import torch
from torch.utils.data import DataLoader

from utils import TextSamplerDataset, MyCollate, ids_to_tokens, BPE_to_eval, epoch_time

from model.xtransformer import XTransformer

from accelerate import Accelerator

import sacrebleu

def main():

    accelerator = Accelerator()

    device = accelerator.device

    with open('dataset/nl/wmt17_en_de/vocabulary.json', 'r') as f:
        vocabulary = json.load(f)

    # Get the size of the JSON object
    NUM_TOKENS = len(vocabulary.keys())

    # constants

    EPOCHS = 300
    BATCH_SIZE = 32
    LEARNING_RATE = 3e-4
    GENERATE_EVERY  = 100
    ENC_SEQ_LEN = 100
    DEC_SEQ_LEN = 100
    MAX_LEN = 100
    WARMUP_STEP = 50

    model = XTransformer(
        dim = 512,
        tie_token_embeds = True,
        return_tgt_loss = True,
        enc_num_tokens=NUM_TOKENS,
        enc_depth = 3,
        enc_heads = 8,
        enc_max_seq_len = ENC_SEQ_LEN,
        dec_num_tokens = NUM_TOKENS,
        dec_depth = 3,
        dec_heads = 8,
        dec_max_seq_len = DEC_SEQ_LEN
    ).to(device)

    with gzip.open('dataset/nl/wmt17_en_de/train.en.ids.gz', 'r') as file:
        X_train = file.read()
        X_train = X_train.decode(encoding='utf-8')
        X_train = X_train.split('\n')
        X_train = [np.array([int(x) for x in line.split()]) for line in X_train]

    with gzip.open('dataset/nl/wmt17_en_de/train.de.ids.gz', 'r') as file:
        Y_train = file.read()
        Y_train = Y_train.decode(encoding='utf-8')
        Y_train = Y_train.split('\n')
        Y_train = [np.array([int(x) for x in line.split()]) for line in Y_train]

    with gzip.open('dataset/nl/wmt17_en_de/valid.en.ids.gz', 'r') as file:
        X_dev = file.read()
        X_dev = X_dev.decode(encoding='utf-8')
        X_dev = X_dev.split('\n')
        X_dev = [np.array([int(x) for x in line.split()]) for line in X_dev]

    with gzip.open('dataset/nl/wmt17_en_de/valid.de.ids.gz', 'r') as file:
        Y_dev = file.read()
        Y_dev = Y_dev.decode(encoding='utf-8')
        Y_dev = Y_dev.split('\n')
        Y_dev = [np.array([int(x) for x in line.split()]) for line in Y_dev]


    train_dataset = TextSamplerDataset(X_train, Y_train, MAX_LEN)
    train_loader  = DataLoader(train_dataset, batch_size = BATCH_SIZE, num_workers=0, shuffle=True,
                           pin_memory=True, collate_fn=MyCollate(pad_idx=3))
    dev_dataset = TextSamplerDataset(X_dev, Y_dev, MAX_LEN)
    dev_loader  = DataLoader(dev_dataset, batch_size=1, num_workers=0)

    # optimizer
    optimizer = get_optimizer(model.parameters(), LEARNING_RATE, wd=0.01)
    scheduler = get_constant_schedule_with_warmup(optimizer, num_warmup_steps=WARMUP_STEP)

    model, optimizer, trainloader = accelerator.prepare(model, optim, train_loader)

    report_loss = 0.
    best_bleu = 0

    # training
    for i in tqdm.tqdm(range(EPOCHS), desc='training'):
        start_time = time.time()
        model.train()

        for src, tgt in train_loader:

            mask_src = src != 3

            loss = model(src, tgt.type(torch.LongTensor), mask_src=mask_src)
            accelerator.backward(loss)

            report_loss += loss

            optim.zero_grad()

            optim.step()
            scheduler.step()

        print('[Epoch %d] epoch elapsed %ds' % (i, time.time() - start_time))

        log_str = '[EPOCH %d] loss_train=%.5f' % (i, report_loss)

        print(log_str)

        report_loss = 0

        if i != 0 and i % GENERATE_EVERY == 0:

            model.eval()
            target = []
            predicted = []
            for src, tgt in dev_loader:
                start_tokens = (torch.ones((1, 1)) * 1).long()

                sample = model.generate(src, start_tokens, MAX_LEN)

                print(f"input:  ", src)
                print(f"target:", tgt)
                print(f"predicted output:  ", sample)

                target.append(ids_to_tokens(tgt.tolist()[0], vocabulary))
                predicted.append(ids_to_tokens(sample.tolist()[0], vocabulary))

            target_bleu = [BPE_to_eval(sentence) for sentence in target]

            predicted_bleu = [BPE_to_eval(sentence) for sentence in predicted]

            end_time = time.time()

            epoch_mins, epoch_secs = epoch_time(start_time, end_time)

            bleu = sacrebleu.corpus_bleu(predicted_bleu, [target_bleu])
            bleu = bleu.score
            print('Epoch: {0} | Time: {1}m {2}s, bleu score = {3}'.format(i, epoch_mins, epoch_secs, bleu))

            if bleu > best_bleu:
                best_bleu = bleu
                torch.save(model.state_dict(),
                           'output/model_seq2seq.pt'
                           )

                torch.save(optimizer.state_dict(), 'output/optim.bin')


if __name__ == '__main__':
    main()