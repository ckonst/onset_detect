# -*- coding: utf-8 -*-

import librosa as lb
import numpy as np
import unittest
import torch

from evaluation import model_eval
from onset_detect import get_lmfs

class TrainingTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_audio, cls.fs = lb.load('./audio/pop_shuffle.wav')
        cls.test_onsets = np.load('./test/onsets.npy')
        cls.clicks, fs = lb.load('./audio/click_track.wav')
        fs = cls.fs
        cls.test_spectrogram = get_lmfs(
            fs, cls.test_audio, 1024, int(0.001 * fs), 20.0, 0.5 * fs)

    def run_basic_test(self, ndim, fn, *args):
        x = torch.tensor([0,0,0,0,0,0,0,0])
        y = torch.tensor([0,0,0,0,0,0,0,0])
        if ndim > 1:
            x = x.unsqueeze(0)
            y = y.unsqueeze(0)
        assert fn(x, y, *args)\
            == (0.0, 0.0, 0.0)
        x = torch.tensor([1,0,1,0,1,0,1,0])
        y = torch.tensor([1,0,0,1,1,0,1,1])
        if ndim > 1:
            x = x.unsqueeze(0)
            y = y.unsqueeze(0)
        assert fn(x, y, *args)\
            == (1.0, 1.0, 1.0)

    def test_evaluate(self):
        pass

    def test_evaluate_batch(self):
        self.run_basic_test(2, model_eval.evaluate_batch, 0.01, 100, 1)

    def test_evaluate_frame(self):
        self.run_basic_test(1, model_eval.evaluate_frame, 0.01, 100, 1)

    def test_evaluate_frame_naive(self):
        self.run_basic_test(1, model_eval.evaluate_frame_naive)

    def test_fscore_precision_recall(self):
        tp, fp, fn = 100, 300, 400
        assert model_eval.fscore_precision_recall(tp, fp, fn)\
            == (0.2222222222222222, 0.25, 0.2)
        tp, fp, fn = 0, 0, 0
        assert model_eval.fscore_precision_recall(tp, fp, fn)\
            == (0.0, 0.0, 0.0)

if __name__ == '__main__':
    unittest.main()
