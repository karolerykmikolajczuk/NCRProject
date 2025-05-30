"""Module containing the definition of the evaluation metrics.
The metrics are implemented as static methods of the class :class:`Metrics`.
"""

import logging
import bottleneck as bn
import numpy as np

__all__ = ['Metrics']

logger = logging.getLogger(__name__)

class Metrics(object):
    """The class Metrics contains metric functions.
    All methods are static and no object of type :class:`Metrics` is needed to compute
    the metrics.
    """
    @staticmethod
    def compute(pred_scores, ground_truth, metrics_list):
        """Compute the given list of evaluation metrics.
        The method computes all the metric listed in ``metric_list`` for all the users.
        Parameters
        ----------
        pred_scores : :obj:`numpy.array`
            The array with the predicted scores. Users are on the rows and items on the columns.
        ground_truth : :obj:`numpy.array`
            Binary array with the ground truth. 1 means the item is relevant for the user
            and 0 not relevant. Users are on the rows and items on the columns.
        metrics_list : :obj:`list` of :obj:`str`
            The list of metrics to compute. Metrics are indicated by strings formed in the
            following way:
            ``metric_name`` @ ``k``
            where ``metric_name`` must correspond to one of the
            method names without the suffix '_at_k', and ``k`` is the corresponding parameter of
            the method and it must be an integer value. For example: ``ndcg@10`` is a valid metric
            name and it corresponds to the method :func:`ndcg_at_k` with ``k=10``.
        Returns
        -------
        :obj:`dict` of :obj:`numpy.array`
            Dictionary with the results for each metric in ``metric_list``. Keys are string
            representing the metric, while the value is an array with the value of the metric
            computed for each user.
        """
        results = {}
        for metric in metrics_list:
            try:
                if "@" in metric:
                    met, k = metric.split("@")
                    met_foo = getattr(Metrics, "%s_at_k" % met.lower())
                    results[metric] = met_foo(pred_scores, ground_truth, int(k))
                else:
                    results[metric] = getattr(Metrics, metric)(pred_scores, ground_truth)
            except AttributeError:
                logger.warning("Skipped unknown metric '%s'.", metric)
        return results
    
    @staticmethod
    def _get_top_k_items(pred_scores, k):
        """Pobiera indeksy top-k rekomendowanych elementów dla każdego użytkownika."""
        relevant_indices = bn.argpartition(-pred_scores, k - 1, axis=1)[:, :k]
        return relevant_indices

    @staticmethod
    def _get_relevant_items_for_user(ground_truth_row):
        """Pobiera listę indeksów relewantnych elementów dla danego użytkownika."""
        return np.where(ground_truth_row > 0)[0].tolist()

    @staticmethod
    def _get_recommended_items_for_user(pred_scores_row, k):
        """Pobiera listę indeksów top-k rekomendowanych elementów dla danego użytkownika."""
        top_k_indices = np.argsort(-pred_scores_row)[:k].tolist()
        return top_k_indices

    @staticmethod
    def mean_precision_at_k(pred_scores, ground_truth, k=5):
        """
        Zmodyfikowana wersja mean_precision_at_k przyjmująca macierze wyników i ground truth.
        """
        if pred_scores.shape[0] != ground_truth.shape[0]:
            raise ValueError("Liczba wierszy w pred_scores musi być równa liczbie wierszy w ground_truth.")

        precision_scores = []
        for user_idx in range(pred_scores.shape[0]):
            recommended_indices = Metrics._get_recommended_items_for_user(pred_scores[user_idx], k)
            relevant_indices = Metrics._get_relevant_items_for_user(ground_truth[user_idx])

            top_k_recommended = recommended_indices[:k]
            relevant_in_top_k = [item for item in top_k_recommended if item in relevant_indices]

            if len(top_k_recommended) > 0:
                precision = len(relevant_in_top_k) / len(top_k_recommended)
            else:
                precision = 0.0
            precision_scores.append(precision)

        return np.mean(precision_scores)

    @staticmethod
    def mean_recall_at_k(pred_scores, ground_truth, k=5):
        """
        Zmodyfikowana wersja mean_recall_at_k przyjmująca macierze wyników i ground truth.
        """
        if pred_scores.shape[0] != ground_truth.shape[0]:
            raise ValueError("Liczba wierszy w pred_scores musi być równa liczbie wierszy w ground_truth.")

        recall_scores = []
        for user_idx in range(pred_scores.shape[0]):
            recommended_indices = Metrics._get_recommended_items_for_user(pred_scores[user_idx], k)
            relevant_indices = Metrics._get_relevant_items_for_user(ground_truth[user_idx])

            top_k_recommended = recommended_indices[:k]
            relevant_in_top_k = [item for item in top_k_recommended if item in relevant_indices]

            if len(relevant_indices) > 0:
                recall = len(relevant_in_top_k) / len(relevant_indices)
            else:
                recall = 0.0
            recall_scores.append(recall)

        return np.mean(recall_scores)

    @staticmethod
    def mean_average_precision_at_k(pred_scores, ground_truth, k=5):
        """
        Zmodyfikowana wersja mean_average_precision_at_k przyjmująca macierze wyników i ground truth.
        """
        if pred_scores.shape[0] != ground_truth.shape[0]:
            raise ValueError("Liczba wierszy w pred_scores musi być równa liczbie wierszy w ground_truth.")

        apk_scores = []
        for user_idx in range(pred_scores.shape[0]):
            recommended_indices = Metrics._get_recommended_items_for_user(pred_scores[user_idx], k)
            relevant_indices = Metrics._get_relevant_items_for_user(ground_truth[user_idx])

            relevant_in_top_k = [(i + 1, item) for i, item in enumerate(recommended_indices[:k]) if item in relevant_indices]

            if not relevant_indices:
                apk = 0.0
            elif not relevant_in_top_k:
                apk = 0.0
            else:
                precision_sum = 0.0
                for rank, item in relevant_in_top_k:
                    top_n = recommended_indices[:rank]
                    relevant_at_rank = [r for r in top_n if r in relevant_indices]
                    precision_at_rank = len(relevant_at_rank) / len(top_n) if len(top_n) > 0 else 0.0
                    precision_sum += precision_at_rank
                apk = precision_sum / len(relevant_indices)
            apk_scores.append(apk)

        return np.mean(apk_scores)

    @staticmethod
    def position_aware_recall_at_k(pred_scores, ground_truth, k=100):
        assert pred_scores.shape == ground_truth.shape, \
            "'pred_scores' and 'ground_truth' must have the same shape."
        k = min(pred_scores.shape[1], k)
        n_users = pred_scores.shape[0]
        position_aware_recall_scores = []

        for user_idx in range(n_users):
            relevant_indices = np.where(ground_truth[user_idx] > 0)[0]
            if not relevant_indices.size:
                position_aware_recall_scores.append(0.0)
                continue

            ranked_predictions = np.argsort(-pred_scores[user_idx])[:k]
            hit_positions = []
            for i, pred_index in enumerate(ranked_predictions):
                if pred_index in relevant_indices:
                    hit_positions.append(i + 1)

            position_reward = sum(1.0 / pos for pos in hit_positions) if hit_positions else 0.0
            position_aware_recall = position_reward / len(relevant_indices) if relevant_indices.size > 0 else 0.0
            position_aware_recall_scores.append(position_aware_recall)

        return np.array(position_aware_recall_scores)

    @staticmethod
    def ndcg_at_k(pred_scores, ground_truth, k=100):
        """Compute the Normalized Discount Cumulative Gain (nDCG).
        nDCG is a measure of ranking quality. nDCG measures the usefulness, or gain, of an
        item based on its position in the scoring list. The gain is accumulated from the top of
        the result list to the bottom, with the gain of each result discounted at lower ranks.
        The nDCG is computed over the top-k items (out of :math:`m`), where `k` is specified as a
        parameter, for all users independently.
        The nDCG@k (:math:`k \in [1,2,\dots,m]`) is computed with the following formula:
        :math:`nDCG@k = \frac{\textrm{DCG}@k}{\textrm{IDCG}@k}`
        where
        :math:`\textrm{DCG}@k = \sum\limits_{i=1}^k \frac{2^{rel_i}-1}{\log_2 (i+1)},`
        :math:`\textrm{IDCG}@k = \sum\limits_{i=1}^{\min(k,R)} \frac{1}{\log_2 (i+1)}`
        with
        :math:`rel_i \in \{0,1\}`
        indicates whether the item at *i*-th position in the ranking is relevant or not,
        and *R* is the number of relevant items.
        Parameters
        ----------
        pred_scores : :obj:`numpy.array`
            The array with the predicted scores. Users are on the rows and items on the columns.
        ground_truth : :obj:`numpy.array`
            Binary array with the ground truth items. 1 means the item is relevant for the user
            and 0 not relevant. Users are on the rows and items on the columns.
        k : :obj:`int` [optional]
            The number of top items to considers, by default 100
        Returns
        -------
        :obj:`numpy.array`
            An array containing the *ndcg@k* value for each user.
        """
        assert pred_scores.shape == ground_truth.shape,\
            "'pred_scores' and 'ground_truth' must have the same shape."
        k = min(pred_scores.shape[1], k)
        n_users = pred_scores.shape[0]
        idx_topk_part = bn.argpartition(-pred_scores, k-1, axis=1)
        topk_part = pred_scores[np.arange(n_users)[:, np.newaxis], idx_topk_part[:, :k]]
        idx_part = np.argsort(-topk_part, axis=1)
        idx_topk = idx_topk_part[np.arange(n_users)[:, np.newaxis], idx_part]
        tp = 1. / np.log2(np.arange(2, k + 2))
        DCG = (ground_truth[np.arange(n_users)[:, np.newaxis], idx_topk] * tp).sum(axis=1)
        IDCG = np.array([(tp[:min(int(n), k)]).sum() for n in ground_truth.sum(axis=1)])
        return DCG / IDCG

    @staticmethod
    def recall_at_k(pred_scores, ground_truth, k=100):
        """Compute the Recall.
        The recall@k is the fraction of the relevant items that are successfully scored in the top-k
        The recall is computed over the top-k items (out of :math:`m`), where `k` is specified as a
        parameter, for all users independently.
        Recall@k is computed as
        :math:`\textrm{recall}@k = \frac{\textrm{TP}}{\textrm{TP}+\textrm{FN}}`
        where TP and FN are the true positive and the false negative retrieved items, respectively.
        Parameters
        ----------
        pred_scores : :obj:`numpy.array`
            The array with the predicted scores. Users are on the rows and items on the columns.
        ground_truth : :obj:`numpy.array`
            Binary array with the ground truth. 1 means the item is relevant for the user
            and 0 not relevant. Users are on the rows and items on the columns.
        k : :obj:`int` [optional]
            The number of top items to considers, by default 100
        Returns
        -------
        :obj:`numpy.array`
            An array containing the *recall@k* value for each user.
        """
        assert pred_scores.shape == ground_truth.shape,\
            "'pred_scores' and 'ground_truth' must have the same shape."
        k = min(pred_scores.shape[1], k)
        idx = bn.argpartition(-pred_scores, k-1, axis=1)
        pred_scores_binary = np.zeros_like(pred_scores, dtype=bool)
        pred_scores_binary[np.arange(pred_scores.shape[0])[:, np.newaxis], idx[:, :k]] = True
        X_true_binary = (ground_truth > 0)
        num = (np.logical_and(X_true_binary, pred_scores_binary).sum(axis=1)).astype(np.float32)
        recall = num / np.minimum(k, X_true_binary.sum(axis=1))
        return recall

    @staticmethod
    def hit_at_k(pred_scores, ground_truth, k=100):
        """Compute the hit at k.
        The Hit@k is either 1, if a relevan item is in the top *k* scored items, or 0 otherwise.
        Parameters
        ----------
        pred_scores : :obj:`numpy.array`
            The array with the predicted scores. Users are on the rows and items on the columns.
        ground_truth : :obj:`numpy.array`
            Binary array with the ground truth. 1 means the item is relevant for the user
            and 0 not relevant. Users are on the rows and items on the columns.
        k : :obj:`int` [optional]
            The number of top items to considers, by default 100
        Returns
        -------
        :obj:`numpy.array`
            An array containing the *hit@k* value for each user.
        """
        assert pred_scores.shape == ground_truth.shape,\
            "'pred_scores' and 'ground_truth' must have the same shape."
        k = min(pred_scores.shape[1], k)
        idx = bn.argpartition(-pred_scores, k-1, axis=1)
        pred_scores_binary = np.zeros_like(pred_scores, dtype=bool)
        pred_scores_binary[np.arange(pred_scores.shape[0])[:, np.newaxis], idx[:, :k]] = True
        X_true_binary = (ground_truth > 0)
        num = (np.logical_and(X_true_binary, pred_scores_binary).sum(axis=1)).astype(np.float32)
        return num > 0