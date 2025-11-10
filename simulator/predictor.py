# predictor.py
import time
from collections import defaultdict, deque

class HotStripePredictor:
    """
    Lightweight frequency-based predictor using sliding window counts.
    When stripe access count >= threshold within window -> mark hot.
    """
    def __init__(self, window_size=1000, threshold=20):
        self.window_size = window_size
        self.threshold = threshold
        self.window = deque()
        self.counts = defaultdict(int)

    def observe(self, stripe_id):
        self.window.append(stripe_id)
        self.counts[stripe_id] += 1
        if len(self.window) > self.window_size:
            removed = self.window.popleft()
            self.counts[removed] -= 1
            if self.counts[removed] <= 0:
                del self.counts[removed]

    def is_hot(self, stripe_id):
        return self.counts.get(stripe_id, 0) >= self.threshold
