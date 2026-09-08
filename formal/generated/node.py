"""Generated executable Python. Source mapping and bounds: manifest.json. Do not edit."""
class Node:
    def __init__(self):
        self.reset()
    def reset(self):
        self.num = 0
        self.promised = -1
        self.accepted_n = -1
        self.accepted = 0
        self.own = 0
        self.pc = 0
        self.status = 0
        self.fault = 0
        self.out_kind = 0
        self.out_target = 0
        self.out_num = 0
        self.out_value = 0
        self.out_prior_n = -1
        self.out_prior_v = 0
        self.declared = 0
        self.declared_num = 0
        self.declared_value = 0
        self.pv_has_0 = 0
        self.pv_0 = 0
        self.prom_has_0 = 0
        self.acc_has_0 = 0
        self.cand_has_0 = 0
        self.next_rank_0 = 0
        self.prom_0_0 = 0
        self.acc_0_0 = 0
        self.prom_0_1 = 0
        self.acc_0_1 = 0
        self.prom_0_2 = 0
        self.acc_0_2 = 0
        self.count_0_1 = 0
        self.rank_0_1 = 0
        self.count_0_2 = 0
        self.rank_0_2 = 0
        self.count_0_3 = 0
        self.rank_0_3 = 0
        self.count_0_4 = 0
        self.rank_0_4 = 0
        self.count_0_5 = 0
        self.rank_0_5 = 0
        self.pv_has_1 = 0
        self.pv_1 = 0
        self.prom_has_1 = 0
        self.acc_has_1 = 0
        self.cand_has_1 = 0
        self.next_rank_1 = 0
        self.prom_1_0 = 0
        self.acc_1_0 = 0
        self.prom_1_1 = 0
        self.acc_1_1 = 0
        self.prom_1_2 = 0
        self.acc_1_2 = 0
        self.count_1_1 = 0
        self.rank_1_1 = 0
        self.count_1_2 = 0
        self.rank_1_2 = 0
        self.count_1_3 = 0
        self.rank_1_3 = 0
        self.count_1_4 = 0
        self.rank_1_4 = 0
        self.count_1_5 = 0
        self.rank_1_5 = 0
        self.pv_has_2 = 0
        self.pv_2 = 0
        self.prom_has_2 = 0
        self.acc_has_2 = 0
        self.cand_has_2 = 0
        self.next_rank_2 = 0
        self.prom_2_0 = 0
        self.acc_2_0 = 0
        self.prom_2_1 = 0
        self.acc_2_1 = 0
        self.prom_2_2 = 0
        self.acc_2_2 = 0
        self.count_2_1 = 0
        self.rank_2_1 = 0
        self.count_2_2 = 0
        self.rank_2_2 = 0
        self.count_2_3 = 0
        self.rank_2_3 = 0
        self.count_2_4 = 0
        self.rank_2_4 = 0
        self.count_2_5 = 0
        self.rank_2_5 = 0
        self.pv_has_3 = 0
        self.pv_3 = 0
        self.prom_has_3 = 0
        self.acc_has_3 = 0
        self.cand_has_3 = 0
        self.next_rank_3 = 0
        self.prom_3_0 = 0
        self.acc_3_0 = 0
        self.prom_3_1 = 0
        self.acc_3_1 = 0
        self.prom_3_2 = 0
        self.acc_3_2 = 0
        self.count_3_1 = 0
        self.rank_3_1 = 0
        self.count_3_2 = 0
        self.rank_3_2 = 0
        self.count_3_3 = 0
        self.rank_3_3 = 0
        self.count_3_4 = 0
        self.rank_3_4 = 0
        self.count_3_5 = 0
        self.rank_3_5 = 0
        self.pv_has_4 = 0
        self.pv_4 = 0
        self.prom_has_4 = 0
        self.acc_has_4 = 0
        self.cand_has_4 = 0
        self.next_rank_4 = 0
        self.prom_4_0 = 0
        self.acc_4_0 = 0
        self.prom_4_1 = 0
        self.acc_4_1 = 0
        self.prom_4_2 = 0
        self.acc_4_2 = 0
        self.count_4_1 = 0
        self.rank_4_1 = 0
        self.count_4_2 = 0
        self.rank_4_2 = 0
        self.count_4_3 = 0
        self.rank_4_3 = 0
        self.count_4_4 = 0
        self.rank_4_4 = 0
        self.count_4_5 = 0
        self.rank_4_5 = 0
        self.pv_has_5 = 0
        self.pv_5 = 0
        self.prom_has_5 = 0
        self.acc_has_5 = 0
        self.cand_has_5 = 0
        self.next_rank_5 = 0
        self.prom_5_0 = 0
        self.acc_5_0 = 0
        self.prom_5_1 = 0
        self.acc_5_1 = 0
        self.prom_5_2 = 0
        self.acc_5_2 = 0
        self.count_5_1 = 0
        self.rank_5_1 = 0
        self.count_5_2 = 0
        self.rank_5_2 = 0
        self.count_5_3 = 0
        self.rank_5_3 = 0
        self.count_5_4 = 0
        self.rank_5_4 = 0
        self.count_5_5 = 0
        self.rank_5_5 = 0
        self.pv_has_6 = 0
        self.pv_6 = 0
        self.prom_has_6 = 0
        self.acc_has_6 = 0
        self.cand_has_6 = 0
        self.next_rank_6 = 0
        self.prom_6_0 = 0
        self.acc_6_0 = 0
        self.prom_6_1 = 0
        self.acc_6_1 = 0
        self.prom_6_2 = 0
        self.acc_6_2 = 0
        self.count_6_1 = 0
        self.rank_6_1 = 0
        self.count_6_2 = 0
        self.rank_6_2 = 0
        self.count_6_3 = 0
        self.rank_6_3 = 0
        self.count_6_4 = 0
        self.rank_6_4 = 0
        self.count_6_5 = 0
        self.rank_6_5 = 0
        self.pv_has_7 = 0
        self.pv_7 = 0
        self.prom_has_7 = 0
        self.acc_has_7 = 0
        self.cand_has_7 = 0
        self.next_rank_7 = 0
        self.prom_7_0 = 0
        self.acc_7_0 = 0
        self.prom_7_1 = 0
        self.acc_7_1 = 0
        self.prom_7_2 = 0
        self.acc_7_2 = 0
        self.count_7_1 = 0
        self.rank_7_1 = 0
        self.count_7_2 = 0
        self.rank_7_2 = 0
        self.count_7_3 = 0
        self.rank_7_3 = 0
        self.count_7_4 = 0
        self.rank_7_4 = 0
        self.count_7_5 = 0
        self.rank_7_5 = 0
        self.pv_has_8 = 0
        self.pv_8 = 0
        self.prom_has_8 = 0
        self.acc_has_8 = 0
        self.cand_has_8 = 0
        self.next_rank_8 = 0
        self.prom_8_0 = 0
        self.acc_8_0 = 0
        self.prom_8_1 = 0
        self.acc_8_1 = 0
        self.prom_8_2 = 0
        self.acc_8_2 = 0
        self.count_8_1 = 0
        self.rank_8_1 = 0
        self.count_8_2 = 0
        self.rank_8_2 = 0
        self.count_8_3 = 0
        self.rank_8_3 = 0
        self.count_8_4 = 0
        self.rank_8_4 = 0
        self.count_8_5 = 0
        self.rank_8_5 = 0
        self.pv_has_9 = 0
        self.pv_9 = 0
        self.prom_has_9 = 0
        self.acc_has_9 = 0
        self.cand_has_9 = 0
        self.next_rank_9 = 0
        self.prom_9_0 = 0
        self.acc_9_0 = 0
        self.prom_9_1 = 0
        self.acc_9_1 = 0
        self.prom_9_2 = 0
        self.acc_9_2 = 0
        self.count_9_1 = 0
        self.rank_9_1 = 0
        self.count_9_2 = 0
        self.rank_9_2 = 0
        self.count_9_3 = 0
        self.rank_9_3 = 0
        self.count_9_4 = 0
        self.rank_9_4 = 0
        self.count_9_5 = 0
        self.rank_9_5 = 0
        self.pv_has_10 = 0
        self.pv_10 = 0
        self.prom_has_10 = 0
        self.acc_has_10 = 0
        self.cand_has_10 = 0
        self.next_rank_10 = 0
        self.prom_10_0 = 0
        self.acc_10_0 = 0
        self.prom_10_1 = 0
        self.acc_10_1 = 0
        self.prom_10_2 = 0
        self.acc_10_2 = 0
        self.count_10_1 = 0
        self.rank_10_1 = 0
        self.count_10_2 = 0
        self.rank_10_2 = 0
        self.count_10_3 = 0
        self.rank_10_3 = 0
        self.count_10_4 = 0
        self.rank_10_4 = 0
        self.count_10_5 = 0
        self.rank_10_5 = 0
        self.pv_has_11 = 0
        self.pv_11 = 0
        self.prom_has_11 = 0
        self.acc_has_11 = 0
        self.cand_has_11 = 0
        self.next_rank_11 = 0
        self.prom_11_0 = 0
        self.acc_11_0 = 0
        self.prom_11_1 = 0
        self.acc_11_1 = 0
        self.prom_11_2 = 0
        self.acc_11_2 = 0
        self.count_11_1 = 0
        self.rank_11_1 = 0
        self.count_11_2 = 0
        self.rank_11_2 = 0
        self.count_11_3 = 0
        self.rank_11_3 = 0
        self.count_11_4 = 0
        self.rank_11_4 = 0
        self.count_11_5 = 0
        self.rank_11_5 = 0
        self.pv_has_12 = 0
        self.pv_12 = 0
        self.prom_has_12 = 0
        self.acc_has_12 = 0
        self.cand_has_12 = 0
        self.next_rank_12 = 0
        self.prom_12_0 = 0
        self.acc_12_0 = 0
        self.prom_12_1 = 0
        self.acc_12_1 = 0
        self.prom_12_2 = 0
        self.acc_12_2 = 0
        self.count_12_1 = 0
        self.rank_12_1 = 0
        self.count_12_2 = 0
        self.rank_12_2 = 0
        self.count_12_3 = 0
        self.rank_12_3 = 0
        self.count_12_4 = 0
        self.rank_12_4 = 0
        self.count_12_5 = 0
        self.rank_12_5 = 0
        self.pv_has_13 = 0
        self.pv_13 = 0
        self.prom_has_13 = 0
        self.acc_has_13 = 0
        self.cand_has_13 = 0
        self.next_rank_13 = 0
        self.prom_13_0 = 0
        self.acc_13_0 = 0
        self.prom_13_1 = 0
        self.acc_13_1 = 0
        self.prom_13_2 = 0
        self.acc_13_2 = 0
        self.count_13_1 = 0
        self.rank_13_1 = 0
        self.count_13_2 = 0
        self.rank_13_2 = 0
        self.count_13_3 = 0
        self.rank_13_3 = 0
        self.count_13_4 = 0
        self.rank_13_4 = 0
        self.count_13_5 = 0
        self.rank_13_5 = 0
        self.pv_has_14 = 0
        self.pv_14 = 0
        self.prom_has_14 = 0
        self.acc_has_14 = 0
        self.cand_has_14 = 0
        self.next_rank_14 = 0
        self.prom_14_0 = 0
        self.acc_14_0 = 0
        self.prom_14_1 = 0
        self.acc_14_1 = 0
        self.prom_14_2 = 0
        self.acc_14_2 = 0
        self.count_14_1 = 0
        self.rank_14_1 = 0
        self.count_14_2 = 0
        self.rank_14_2 = 0
        self.count_14_3 = 0
        self.rank_14_3 = 0
        self.count_14_4 = 0
        self.rank_14_4 = 0
        self.count_14_5 = 0
        self.rank_14_5 = 0
        self.pv_has_15 = 0
        self.pv_15 = 0
        self.prom_has_15 = 0
        self.acc_has_15 = 0
        self.cand_has_15 = 0
        self.next_rank_15 = 0
        self.prom_15_0 = 0
        self.acc_15_0 = 0
        self.prom_15_1 = 0
        self.acc_15_1 = 0
        self.prom_15_2 = 0
        self.acc_15_2 = 0
        self.count_15_1 = 0
        self.rank_15_1 = 0
        self.count_15_2 = 0
        self.rank_15_2 = 0
        self.count_15_3 = 0
        self.rank_15_3 = 0
        self.count_15_4 = 0
        self.rank_15_4 = 0
        self.count_15_5 = 0
        self.rank_15_5 = 0
        self.pv_has_16 = 0
        self.pv_16 = 0
        self.prom_has_16 = 0
        self.acc_has_16 = 0
        self.cand_has_16 = 0
        self.next_rank_16 = 0
        self.prom_16_0 = 0
        self.acc_16_0 = 0
        self.prom_16_1 = 0
        self.acc_16_1 = 0
        self.prom_16_2 = 0
        self.acc_16_2 = 0
        self.count_16_1 = 0
        self.rank_16_1 = 0
        self.count_16_2 = 0
        self.rank_16_2 = 0
        self.count_16_3 = 0
        self.rank_16_3 = 0
        self.count_16_4 = 0
        self.rank_16_4 = 0
        self.count_16_5 = 0
        self.rank_16_5 = 0
        self.pv_has_17 = 0
        self.pv_17 = 0
        self.prom_has_17 = 0
        self.acc_has_17 = 0
        self.cand_has_17 = 0
        self.next_rank_17 = 0
        self.prom_17_0 = 0
        self.acc_17_0 = 0
        self.prom_17_1 = 0
        self.acc_17_1 = 0
        self.prom_17_2 = 0
        self.acc_17_2 = 0
        self.count_17_1 = 0
        self.rank_17_1 = 0
        self.count_17_2 = 0
        self.rank_17_2 = 0
        self.count_17_3 = 0
        self.rank_17_3 = 0
        self.count_17_4 = 0
        self.rank_17_4 = 0
        self.count_17_5 = 0
        self.rank_17_5 = 0
        self.pv_has_18 = 0
        self.pv_18 = 0
        self.prom_has_18 = 0
        self.acc_has_18 = 0
        self.cand_has_18 = 0
        self.next_rank_18 = 0
        self.prom_18_0 = 0
        self.acc_18_0 = 0
        self.prom_18_1 = 0
        self.acc_18_1 = 0
        self.prom_18_2 = 0
        self.acc_18_2 = 0
        self.count_18_1 = 0
        self.rank_18_1 = 0
        self.count_18_2 = 0
        self.rank_18_2 = 0
        self.count_18_3 = 0
        self.rank_18_3 = 0
        self.count_18_4 = 0
        self.rank_18_4 = 0
        self.count_18_5 = 0
        self.rank_18_5 = 0
        self.pv_has_19 = 0
        self.pv_19 = 0
        self.prom_has_19 = 0
        self.acc_has_19 = 0
        self.cand_has_19 = 0
        self.next_rank_19 = 0
        self.prom_19_0 = 0
        self.acc_19_0 = 0
        self.prom_19_1 = 0
        self.acc_19_1 = 0
        self.prom_19_2 = 0
        self.acc_19_2 = 0
        self.count_19_1 = 0
        self.rank_19_1 = 0
        self.count_19_2 = 0
        self.rank_19_2 = 0
        self.count_19_3 = 0
        self.rank_19_3 = 0
        self.count_19_4 = 0
        self.rank_19_4 = 0
        self.count_19_5 = 0
        self.rank_19_5 = 0
        self.pv_has_20 = 0
        self.pv_20 = 0
        self.prom_has_20 = 0
        self.acc_has_20 = 0
        self.cand_has_20 = 0
        self.next_rank_20 = 0
        self.prom_20_0 = 0
        self.acc_20_0 = 0
        self.prom_20_1 = 0
        self.acc_20_1 = 0
        self.prom_20_2 = 0
        self.acc_20_2 = 0
        self.count_20_1 = 0
        self.rank_20_1 = 0
        self.count_20_2 = 0
        self.rank_20_2 = 0
        self.count_20_3 = 0
        self.rank_20_3 = 0
        self.count_20_4 = 0
        self.rank_20_4 = 0
        self.count_20_5 = 0
        self.rank_20_5 = 0
        self.pv_has_21 = 0
        self.pv_21 = 0
        self.prom_has_21 = 0
        self.acc_has_21 = 0
        self.cand_has_21 = 0
        self.next_rank_21 = 0
        self.prom_21_0 = 0
        self.acc_21_0 = 0
        self.prom_21_1 = 0
        self.acc_21_1 = 0
        self.prom_21_2 = 0
        self.acc_21_2 = 0
        self.count_21_1 = 0
        self.rank_21_1 = 0
        self.count_21_2 = 0
        self.rank_21_2 = 0
        self.count_21_3 = 0
        self.rank_21_3 = 0
        self.count_21_4 = 0
        self.rank_21_4 = 0
        self.count_21_5 = 0
        self.rank_21_5 = 0
        self.pv_has_22 = 0
        self.pv_22 = 0
        self.prom_has_22 = 0
        self.acc_has_22 = 0
        self.cand_has_22 = 0
        self.next_rank_22 = 0
        self.prom_22_0 = 0
        self.acc_22_0 = 0
        self.prom_22_1 = 0
        self.acc_22_1 = 0
        self.prom_22_2 = 0
        self.acc_22_2 = 0
        self.count_22_1 = 0
        self.rank_22_1 = 0
        self.count_22_2 = 0
        self.rank_22_2 = 0
        self.count_22_3 = 0
        self.rank_22_3 = 0
        self.count_22_4 = 0
        self.rank_22_4 = 0
        self.count_22_5 = 0
        self.rank_22_5 = 0
        self.pv_has_23 = 0
        self.pv_23 = 0
        self.prom_has_23 = 0
        self.acc_has_23 = 0
        self.cand_has_23 = 0
        self.next_rank_23 = 0
        self.prom_23_0 = 0
        self.acc_23_0 = 0
        self.prom_23_1 = 0
        self.acc_23_1 = 0
        self.prom_23_2 = 0
        self.acc_23_2 = 0
        self.count_23_1 = 0
        self.rank_23_1 = 0
        self.count_23_2 = 0
        self.rank_23_2 = 0
        self.count_23_3 = 0
        self.rank_23_3 = 0
        self.count_23_4 = 0
        self.rank_23_4 = 0
        self.count_23_5 = 0
        self.rank_23_5 = 0
        self.pv_has_24 = 0
        self.pv_24 = 0
        self.prom_has_24 = 0
        self.acc_has_24 = 0
        self.cand_has_24 = 0
        self.next_rank_24 = 0
        self.prom_24_0 = 0
        self.acc_24_0 = 0
        self.prom_24_1 = 0
        self.acc_24_1 = 0
        self.prom_24_2 = 0
        self.acc_24_2 = 0
        self.count_24_1 = 0
        self.rank_24_1 = 0
        self.count_24_2 = 0
        self.rank_24_2 = 0
        self.count_24_3 = 0
        self.rank_24_3 = 0
        self.count_24_4 = 0
        self.rank_24_4 = 0
        self.count_24_5 = 0
        self.rank_24_5 = 0
        self.pv_has_25 = 0
        self.pv_25 = 0
        self.prom_has_25 = 0
        self.acc_has_25 = 0
        self.cand_has_25 = 0
        self.next_rank_25 = 0
        self.prom_25_0 = 0
        self.acc_25_0 = 0
        self.prom_25_1 = 0
        self.acc_25_1 = 0
        self.prom_25_2 = 0
        self.acc_25_2 = 0
        self.count_25_1 = 0
        self.rank_25_1 = 0
        self.count_25_2 = 0
        self.rank_25_2 = 0
        self.count_25_3 = 0
        self.rank_25_3 = 0
        self.count_25_4 = 0
        self.rank_25_4 = 0
        self.count_25_5 = 0
        self.rank_25_5 = 0
        self.pv_has_26 = 0
        self.pv_26 = 0
        self.prom_has_26 = 0
        self.acc_has_26 = 0
        self.cand_has_26 = 0
        self.next_rank_26 = 0
        self.prom_26_0 = 0
        self.acc_26_0 = 0
        self.prom_26_1 = 0
        self.acc_26_1 = 0
        self.prom_26_2 = 0
        self.acc_26_2 = 0
        self.count_26_1 = 0
        self.rank_26_1 = 0
        self.count_26_2 = 0
        self.rank_26_2 = 0
        self.count_26_3 = 0
        self.rank_26_3 = 0
        self.count_26_4 = 0
        self.rank_26_4 = 0
        self.count_26_5 = 0
        self.rank_26_5 = 0
        self.pv_has_27 = 0
        self.pv_27 = 0
        self.prom_has_27 = 0
        self.acc_has_27 = 0
        self.cand_has_27 = 0
        self.next_rank_27 = 0
        self.prom_27_0 = 0
        self.acc_27_0 = 0
        self.prom_27_1 = 0
        self.acc_27_1 = 0
        self.prom_27_2 = 0
        self.acc_27_2 = 0
        self.count_27_1 = 0
        self.rank_27_1 = 0
        self.count_27_2 = 0
        self.rank_27_2 = 0
        self.count_27_3 = 0
        self.rank_27_3 = 0
        self.count_27_4 = 0
        self.rank_27_4 = 0
        self.count_27_5 = 0
        self.rank_27_5 = 0
        self.pv_has_28 = 0
        self.pv_28 = 0
        self.prom_has_28 = 0
        self.acc_has_28 = 0
        self.cand_has_28 = 0
        self.next_rank_28 = 0
        self.prom_28_0 = 0
        self.acc_28_0 = 0
        self.prom_28_1 = 0
        self.acc_28_1 = 0
        self.prom_28_2 = 0
        self.acc_28_2 = 0
        self.count_28_1 = 0
        self.rank_28_1 = 0
        self.count_28_2 = 0
        self.rank_28_2 = 0
        self.count_28_3 = 0
        self.rank_28_3 = 0
        self.count_28_4 = 0
        self.rank_28_4 = 0
        self.count_28_5 = 0
        self.rank_28_5 = 0
        self.pv_has_29 = 0
        self.pv_29 = 0
        self.prom_has_29 = 0
        self.acc_has_29 = 0
        self.cand_has_29 = 0
        self.next_rank_29 = 0
        self.prom_29_0 = 0
        self.acc_29_0 = 0
        self.prom_29_1 = 0
        self.acc_29_1 = 0
        self.prom_29_2 = 0
        self.acc_29_2 = 0
        self.count_29_1 = 0
        self.rank_29_1 = 0
        self.count_29_2 = 0
        self.rank_29_2 = 0
        self.count_29_3 = 0
        self.rank_29_3 = 0
        self.count_29_4 = 0
        self.rank_29_4 = 0
        self.count_29_5 = 0
        self.rank_29_5 = 0
        self.pv_has_30 = 0
        self.pv_30 = 0
        self.prom_has_30 = 0
        self.acc_has_30 = 0
        self.cand_has_30 = 0
        self.next_rank_30 = 0
        self.prom_30_0 = 0
        self.acc_30_0 = 0
        self.prom_30_1 = 0
        self.acc_30_1 = 0
        self.prom_30_2 = 0
        self.acc_30_2 = 0
        self.count_30_1 = 0
        self.rank_30_1 = 0
        self.count_30_2 = 0
        self.rank_30_2 = 0
        self.count_30_3 = 0
        self.rank_30_3 = 0
        self.count_30_4 = 0
        self.rank_30_4 = 0
        self.count_30_5 = 0
        self.rank_30_5 = 0
        self.pv_has_31 = 0
        self.pv_31 = 0
        self.prom_has_31 = 0
        self.acc_has_31 = 0
        self.cand_has_31 = 0
        self.next_rank_31 = 0
        self.prom_31_0 = 0
        self.acc_31_0 = 0
        self.prom_31_1 = 0
        self.acc_31_1 = 0
        self.prom_31_2 = 0
        self.acc_31_2 = 0
        self.count_31_1 = 0
        self.rank_31_1 = 0
        self.count_31_2 = 0
        self.rank_31_2 = 0
        self.count_31_3 = 0
        self.rank_31_3 = 0
        self.count_31_4 = 0
        self.rank_31_4 = 0
        self.count_31_5 = 0
        self.rank_31_5 = 0
        return 0
    def step(self, event, sender, number, value, prior_number, prior_value):
        self.num = self.num
        self.promised = self.promised
        self.accepted_n = self.accepted_n
        self.accepted = self.accepted
        self.own = self.own
        self.pc = self.pc
        self.status = self.status
        self.fault = self.fault
        self.out_kind = self.out_kind
        self.out_target = self.out_target
        self.out_num = self.out_num
        self.out_value = self.out_value
        self.out_prior_n = self.out_prior_n
        self.out_prior_v = self.out_prior_v
        self.declared = self.declared
        self.declared_num = self.declared_num
        self.declared_value = self.declared_value
        self.pv_has_0 = self.pv_has_0
        self.pv_0 = self.pv_0
        self.prom_has_0 = self.prom_has_0
        self.acc_has_0 = self.acc_has_0
        self.cand_has_0 = self.cand_has_0
        self.next_rank_0 = self.next_rank_0
        self.prom_0_0 = self.prom_0_0
        self.acc_0_0 = self.acc_0_0
        self.prom_0_1 = self.prom_0_1
        self.acc_0_1 = self.acc_0_1
        self.prom_0_2 = self.prom_0_2
        self.acc_0_2 = self.acc_0_2
        self.count_0_1 = self.count_0_1
        self.rank_0_1 = self.rank_0_1
        self.count_0_2 = self.count_0_2
        self.rank_0_2 = self.rank_0_2
        self.count_0_3 = self.count_0_3
        self.rank_0_3 = self.rank_0_3
        self.count_0_4 = self.count_0_4
        self.rank_0_4 = self.rank_0_4
        self.count_0_5 = self.count_0_5
        self.rank_0_5 = self.rank_0_5
        self.pv_has_1 = self.pv_has_1
        self.pv_1 = self.pv_1
        self.prom_has_1 = self.prom_has_1
        self.acc_has_1 = self.acc_has_1
        self.cand_has_1 = self.cand_has_1
        self.next_rank_1 = self.next_rank_1
        self.prom_1_0 = self.prom_1_0
        self.acc_1_0 = self.acc_1_0
        self.prom_1_1 = self.prom_1_1
        self.acc_1_1 = self.acc_1_1
        self.prom_1_2 = self.prom_1_2
        self.acc_1_2 = self.acc_1_2
        self.count_1_1 = self.count_1_1
        self.rank_1_1 = self.rank_1_1
        self.count_1_2 = self.count_1_2
        self.rank_1_2 = self.rank_1_2
        self.count_1_3 = self.count_1_3
        self.rank_1_3 = self.rank_1_3
        self.count_1_4 = self.count_1_4
        self.rank_1_4 = self.rank_1_4
        self.count_1_5 = self.count_1_5
        self.rank_1_5 = self.rank_1_5
        self.pv_has_2 = self.pv_has_2
        self.pv_2 = self.pv_2
        self.prom_has_2 = self.prom_has_2
        self.acc_has_2 = self.acc_has_2
        self.cand_has_2 = self.cand_has_2
        self.next_rank_2 = self.next_rank_2
        self.prom_2_0 = self.prom_2_0
        self.acc_2_0 = self.acc_2_0
        self.prom_2_1 = self.prom_2_1
        self.acc_2_1 = self.acc_2_1
        self.prom_2_2 = self.prom_2_2
        self.acc_2_2 = self.acc_2_2
        self.count_2_1 = self.count_2_1
        self.rank_2_1 = self.rank_2_1
        self.count_2_2 = self.count_2_2
        self.rank_2_2 = self.rank_2_2
        self.count_2_3 = self.count_2_3
        self.rank_2_3 = self.rank_2_3
        self.count_2_4 = self.count_2_4
        self.rank_2_4 = self.rank_2_4
        self.count_2_5 = self.count_2_5
        self.rank_2_5 = self.rank_2_5
        self.pv_has_3 = self.pv_has_3
        self.pv_3 = self.pv_3
        self.prom_has_3 = self.prom_has_3
        self.acc_has_3 = self.acc_has_3
        self.cand_has_3 = self.cand_has_3
        self.next_rank_3 = self.next_rank_3
        self.prom_3_0 = self.prom_3_0
        self.acc_3_0 = self.acc_3_0
        self.prom_3_1 = self.prom_3_1
        self.acc_3_1 = self.acc_3_1
        self.prom_3_2 = self.prom_3_2
        self.acc_3_2 = self.acc_3_2
        self.count_3_1 = self.count_3_1
        self.rank_3_1 = self.rank_3_1
        self.count_3_2 = self.count_3_2
        self.rank_3_2 = self.rank_3_2
        self.count_3_3 = self.count_3_3
        self.rank_3_3 = self.rank_3_3
        self.count_3_4 = self.count_3_4
        self.rank_3_4 = self.rank_3_4
        self.count_3_5 = self.count_3_5
        self.rank_3_5 = self.rank_3_5
        self.pv_has_4 = self.pv_has_4
        self.pv_4 = self.pv_4
        self.prom_has_4 = self.prom_has_4
        self.acc_has_4 = self.acc_has_4
        self.cand_has_4 = self.cand_has_4
        self.next_rank_4 = self.next_rank_4
        self.prom_4_0 = self.prom_4_0
        self.acc_4_0 = self.acc_4_0
        self.prom_4_1 = self.prom_4_1
        self.acc_4_1 = self.acc_4_1
        self.prom_4_2 = self.prom_4_2
        self.acc_4_2 = self.acc_4_2
        self.count_4_1 = self.count_4_1
        self.rank_4_1 = self.rank_4_1
        self.count_4_2 = self.count_4_2
        self.rank_4_2 = self.rank_4_2
        self.count_4_3 = self.count_4_3
        self.rank_4_3 = self.rank_4_3
        self.count_4_4 = self.count_4_4
        self.rank_4_4 = self.rank_4_4
        self.count_4_5 = self.count_4_5
        self.rank_4_5 = self.rank_4_5
        self.pv_has_5 = self.pv_has_5
        self.pv_5 = self.pv_5
        self.prom_has_5 = self.prom_has_5
        self.acc_has_5 = self.acc_has_5
        self.cand_has_5 = self.cand_has_5
        self.next_rank_5 = self.next_rank_5
        self.prom_5_0 = self.prom_5_0
        self.acc_5_0 = self.acc_5_0
        self.prom_5_1 = self.prom_5_1
        self.acc_5_1 = self.acc_5_1
        self.prom_5_2 = self.prom_5_2
        self.acc_5_2 = self.acc_5_2
        self.count_5_1 = self.count_5_1
        self.rank_5_1 = self.rank_5_1
        self.count_5_2 = self.count_5_2
        self.rank_5_2 = self.rank_5_2
        self.count_5_3 = self.count_5_3
        self.rank_5_3 = self.rank_5_3
        self.count_5_4 = self.count_5_4
        self.rank_5_4 = self.rank_5_4
        self.count_5_5 = self.count_5_5
        self.rank_5_5 = self.rank_5_5
        self.pv_has_6 = self.pv_has_6
        self.pv_6 = self.pv_6
        self.prom_has_6 = self.prom_has_6
        self.acc_has_6 = self.acc_has_6
        self.cand_has_6 = self.cand_has_6
        self.next_rank_6 = self.next_rank_6
        self.prom_6_0 = self.prom_6_0
        self.acc_6_0 = self.acc_6_0
        self.prom_6_1 = self.prom_6_1
        self.acc_6_1 = self.acc_6_1
        self.prom_6_2 = self.prom_6_2
        self.acc_6_2 = self.acc_6_2
        self.count_6_1 = self.count_6_1
        self.rank_6_1 = self.rank_6_1
        self.count_6_2 = self.count_6_2
        self.rank_6_2 = self.rank_6_2
        self.count_6_3 = self.count_6_3
        self.rank_6_3 = self.rank_6_3
        self.count_6_4 = self.count_6_4
        self.rank_6_4 = self.rank_6_4
        self.count_6_5 = self.count_6_5
        self.rank_6_5 = self.rank_6_5
        self.pv_has_7 = self.pv_has_7
        self.pv_7 = self.pv_7
        self.prom_has_7 = self.prom_has_7
        self.acc_has_7 = self.acc_has_7
        self.cand_has_7 = self.cand_has_7
        self.next_rank_7 = self.next_rank_7
        self.prom_7_0 = self.prom_7_0
        self.acc_7_0 = self.acc_7_0
        self.prom_7_1 = self.prom_7_1
        self.acc_7_1 = self.acc_7_1
        self.prom_7_2 = self.prom_7_2
        self.acc_7_2 = self.acc_7_2
        self.count_7_1 = self.count_7_1
        self.rank_7_1 = self.rank_7_1
        self.count_7_2 = self.count_7_2
        self.rank_7_2 = self.rank_7_2
        self.count_7_3 = self.count_7_3
        self.rank_7_3 = self.rank_7_3
        self.count_7_4 = self.count_7_4
        self.rank_7_4 = self.rank_7_4
        self.count_7_5 = self.count_7_5
        self.rank_7_5 = self.rank_7_5
        self.pv_has_8 = self.pv_has_8
        self.pv_8 = self.pv_8
        self.prom_has_8 = self.prom_has_8
        self.acc_has_8 = self.acc_has_8
        self.cand_has_8 = self.cand_has_8
        self.next_rank_8 = self.next_rank_8
        self.prom_8_0 = self.prom_8_0
        self.acc_8_0 = self.acc_8_0
        self.prom_8_1 = self.prom_8_1
        self.acc_8_1 = self.acc_8_1
        self.prom_8_2 = self.prom_8_2
        self.acc_8_2 = self.acc_8_2
        self.count_8_1 = self.count_8_1
        self.rank_8_1 = self.rank_8_1
        self.count_8_2 = self.count_8_2
        self.rank_8_2 = self.rank_8_2
        self.count_8_3 = self.count_8_3
        self.rank_8_3 = self.rank_8_3
        self.count_8_4 = self.count_8_4
        self.rank_8_4 = self.rank_8_4
        self.count_8_5 = self.count_8_5
        self.rank_8_5 = self.rank_8_5
        self.pv_has_9 = self.pv_has_9
        self.pv_9 = self.pv_9
        self.prom_has_9 = self.prom_has_9
        self.acc_has_9 = self.acc_has_9
        self.cand_has_9 = self.cand_has_9
        self.next_rank_9 = self.next_rank_9
        self.prom_9_0 = self.prom_9_0
        self.acc_9_0 = self.acc_9_0
        self.prom_9_1 = self.prom_9_1
        self.acc_9_1 = self.acc_9_1
        self.prom_9_2 = self.prom_9_2
        self.acc_9_2 = self.acc_9_2
        self.count_9_1 = self.count_9_1
        self.rank_9_1 = self.rank_9_1
        self.count_9_2 = self.count_9_2
        self.rank_9_2 = self.rank_9_2
        self.count_9_3 = self.count_9_3
        self.rank_9_3 = self.rank_9_3
        self.count_9_4 = self.count_9_4
        self.rank_9_4 = self.rank_9_4
        self.count_9_5 = self.count_9_5
        self.rank_9_5 = self.rank_9_5
        self.pv_has_10 = self.pv_has_10
        self.pv_10 = self.pv_10
        self.prom_has_10 = self.prom_has_10
        self.acc_has_10 = self.acc_has_10
        self.cand_has_10 = self.cand_has_10
        self.next_rank_10 = self.next_rank_10
        self.prom_10_0 = self.prom_10_0
        self.acc_10_0 = self.acc_10_0
        self.prom_10_1 = self.prom_10_1
        self.acc_10_1 = self.acc_10_1
        self.prom_10_2 = self.prom_10_2
        self.acc_10_2 = self.acc_10_2
        self.count_10_1 = self.count_10_1
        self.rank_10_1 = self.rank_10_1
        self.count_10_2 = self.count_10_2
        self.rank_10_2 = self.rank_10_2
        self.count_10_3 = self.count_10_3
        self.rank_10_3 = self.rank_10_3
        self.count_10_4 = self.count_10_4
        self.rank_10_4 = self.rank_10_4
        self.count_10_5 = self.count_10_5
        self.rank_10_5 = self.rank_10_5
        self.pv_has_11 = self.pv_has_11
        self.pv_11 = self.pv_11
        self.prom_has_11 = self.prom_has_11
        self.acc_has_11 = self.acc_has_11
        self.cand_has_11 = self.cand_has_11
        self.next_rank_11 = self.next_rank_11
        self.prom_11_0 = self.prom_11_0
        self.acc_11_0 = self.acc_11_0
        self.prom_11_1 = self.prom_11_1
        self.acc_11_1 = self.acc_11_1
        self.prom_11_2 = self.prom_11_2
        self.acc_11_2 = self.acc_11_2
        self.count_11_1 = self.count_11_1
        self.rank_11_1 = self.rank_11_1
        self.count_11_2 = self.count_11_2
        self.rank_11_2 = self.rank_11_2
        self.count_11_3 = self.count_11_3
        self.rank_11_3 = self.rank_11_3
        self.count_11_4 = self.count_11_4
        self.rank_11_4 = self.rank_11_4
        self.count_11_5 = self.count_11_5
        self.rank_11_5 = self.rank_11_5
        self.pv_has_12 = self.pv_has_12
        self.pv_12 = self.pv_12
        self.prom_has_12 = self.prom_has_12
        self.acc_has_12 = self.acc_has_12
        self.cand_has_12 = self.cand_has_12
        self.next_rank_12 = self.next_rank_12
        self.prom_12_0 = self.prom_12_0
        self.acc_12_0 = self.acc_12_0
        self.prom_12_1 = self.prom_12_1
        self.acc_12_1 = self.acc_12_1
        self.prom_12_2 = self.prom_12_2
        self.acc_12_2 = self.acc_12_2
        self.count_12_1 = self.count_12_1
        self.rank_12_1 = self.rank_12_1
        self.count_12_2 = self.count_12_2
        self.rank_12_2 = self.rank_12_2
        self.count_12_3 = self.count_12_3
        self.rank_12_3 = self.rank_12_3
        self.count_12_4 = self.count_12_4
        self.rank_12_4 = self.rank_12_4
        self.count_12_5 = self.count_12_5
        self.rank_12_5 = self.rank_12_5
        self.pv_has_13 = self.pv_has_13
        self.pv_13 = self.pv_13
        self.prom_has_13 = self.prom_has_13
        self.acc_has_13 = self.acc_has_13
        self.cand_has_13 = self.cand_has_13
        self.next_rank_13 = self.next_rank_13
        self.prom_13_0 = self.prom_13_0
        self.acc_13_0 = self.acc_13_0
        self.prom_13_1 = self.prom_13_1
        self.acc_13_1 = self.acc_13_1
        self.prom_13_2 = self.prom_13_2
        self.acc_13_2 = self.acc_13_2
        self.count_13_1 = self.count_13_1
        self.rank_13_1 = self.rank_13_1
        self.count_13_2 = self.count_13_2
        self.rank_13_2 = self.rank_13_2
        self.count_13_3 = self.count_13_3
        self.rank_13_3 = self.rank_13_3
        self.count_13_4 = self.count_13_4
        self.rank_13_4 = self.rank_13_4
        self.count_13_5 = self.count_13_5
        self.rank_13_5 = self.rank_13_5
        self.pv_has_14 = self.pv_has_14
        self.pv_14 = self.pv_14
        self.prom_has_14 = self.prom_has_14
        self.acc_has_14 = self.acc_has_14
        self.cand_has_14 = self.cand_has_14
        self.next_rank_14 = self.next_rank_14
        self.prom_14_0 = self.prom_14_0
        self.acc_14_0 = self.acc_14_0
        self.prom_14_1 = self.prom_14_1
        self.acc_14_1 = self.acc_14_1
        self.prom_14_2 = self.prom_14_2
        self.acc_14_2 = self.acc_14_2
        self.count_14_1 = self.count_14_1
        self.rank_14_1 = self.rank_14_1
        self.count_14_2 = self.count_14_2
        self.rank_14_2 = self.rank_14_2
        self.count_14_3 = self.count_14_3
        self.rank_14_3 = self.rank_14_3
        self.count_14_4 = self.count_14_4
        self.rank_14_4 = self.rank_14_4
        self.count_14_5 = self.count_14_5
        self.rank_14_5 = self.rank_14_5
        self.pv_has_15 = self.pv_has_15
        self.pv_15 = self.pv_15
        self.prom_has_15 = self.prom_has_15
        self.acc_has_15 = self.acc_has_15
        self.cand_has_15 = self.cand_has_15
        self.next_rank_15 = self.next_rank_15
        self.prom_15_0 = self.prom_15_0
        self.acc_15_0 = self.acc_15_0
        self.prom_15_1 = self.prom_15_1
        self.acc_15_1 = self.acc_15_1
        self.prom_15_2 = self.prom_15_2
        self.acc_15_2 = self.acc_15_2
        self.count_15_1 = self.count_15_1
        self.rank_15_1 = self.rank_15_1
        self.count_15_2 = self.count_15_2
        self.rank_15_2 = self.rank_15_2
        self.count_15_3 = self.count_15_3
        self.rank_15_3 = self.rank_15_3
        self.count_15_4 = self.count_15_4
        self.rank_15_4 = self.rank_15_4
        self.count_15_5 = self.count_15_5
        self.rank_15_5 = self.rank_15_5
        self.pv_has_16 = self.pv_has_16
        self.pv_16 = self.pv_16
        self.prom_has_16 = self.prom_has_16
        self.acc_has_16 = self.acc_has_16
        self.cand_has_16 = self.cand_has_16
        self.next_rank_16 = self.next_rank_16
        self.prom_16_0 = self.prom_16_0
        self.acc_16_0 = self.acc_16_0
        self.prom_16_1 = self.prom_16_1
        self.acc_16_1 = self.acc_16_1
        self.prom_16_2 = self.prom_16_2
        self.acc_16_2 = self.acc_16_2
        self.count_16_1 = self.count_16_1
        self.rank_16_1 = self.rank_16_1
        self.count_16_2 = self.count_16_2
        self.rank_16_2 = self.rank_16_2
        self.count_16_3 = self.count_16_3
        self.rank_16_3 = self.rank_16_3
        self.count_16_4 = self.count_16_4
        self.rank_16_4 = self.rank_16_4
        self.count_16_5 = self.count_16_5
        self.rank_16_5 = self.rank_16_5
        self.pv_has_17 = self.pv_has_17
        self.pv_17 = self.pv_17
        self.prom_has_17 = self.prom_has_17
        self.acc_has_17 = self.acc_has_17
        self.cand_has_17 = self.cand_has_17
        self.next_rank_17 = self.next_rank_17
        self.prom_17_0 = self.prom_17_0
        self.acc_17_0 = self.acc_17_0
        self.prom_17_1 = self.prom_17_1
        self.acc_17_1 = self.acc_17_1
        self.prom_17_2 = self.prom_17_2
        self.acc_17_2 = self.acc_17_2
        self.count_17_1 = self.count_17_1
        self.rank_17_1 = self.rank_17_1
        self.count_17_2 = self.count_17_2
        self.rank_17_2 = self.rank_17_2
        self.count_17_3 = self.count_17_3
        self.rank_17_3 = self.rank_17_3
        self.count_17_4 = self.count_17_4
        self.rank_17_4 = self.rank_17_4
        self.count_17_5 = self.count_17_5
        self.rank_17_5 = self.rank_17_5
        self.pv_has_18 = self.pv_has_18
        self.pv_18 = self.pv_18
        self.prom_has_18 = self.prom_has_18
        self.acc_has_18 = self.acc_has_18
        self.cand_has_18 = self.cand_has_18
        self.next_rank_18 = self.next_rank_18
        self.prom_18_0 = self.prom_18_0
        self.acc_18_0 = self.acc_18_0
        self.prom_18_1 = self.prom_18_1
        self.acc_18_1 = self.acc_18_1
        self.prom_18_2 = self.prom_18_2
        self.acc_18_2 = self.acc_18_2
        self.count_18_1 = self.count_18_1
        self.rank_18_1 = self.rank_18_1
        self.count_18_2 = self.count_18_2
        self.rank_18_2 = self.rank_18_2
        self.count_18_3 = self.count_18_3
        self.rank_18_3 = self.rank_18_3
        self.count_18_4 = self.count_18_4
        self.rank_18_4 = self.rank_18_4
        self.count_18_5 = self.count_18_5
        self.rank_18_5 = self.rank_18_5
        self.pv_has_19 = self.pv_has_19
        self.pv_19 = self.pv_19
        self.prom_has_19 = self.prom_has_19
        self.acc_has_19 = self.acc_has_19
        self.cand_has_19 = self.cand_has_19
        self.next_rank_19 = self.next_rank_19
        self.prom_19_0 = self.prom_19_0
        self.acc_19_0 = self.acc_19_0
        self.prom_19_1 = self.prom_19_1
        self.acc_19_1 = self.acc_19_1
        self.prom_19_2 = self.prom_19_2
        self.acc_19_2 = self.acc_19_2
        self.count_19_1 = self.count_19_1
        self.rank_19_1 = self.rank_19_1
        self.count_19_2 = self.count_19_2
        self.rank_19_2 = self.rank_19_2
        self.count_19_3 = self.count_19_3
        self.rank_19_3 = self.rank_19_3
        self.count_19_4 = self.count_19_4
        self.rank_19_4 = self.rank_19_4
        self.count_19_5 = self.count_19_5
        self.rank_19_5 = self.rank_19_5
        self.pv_has_20 = self.pv_has_20
        self.pv_20 = self.pv_20
        self.prom_has_20 = self.prom_has_20
        self.acc_has_20 = self.acc_has_20
        self.cand_has_20 = self.cand_has_20
        self.next_rank_20 = self.next_rank_20
        self.prom_20_0 = self.prom_20_0
        self.acc_20_0 = self.acc_20_0
        self.prom_20_1 = self.prom_20_1
        self.acc_20_1 = self.acc_20_1
        self.prom_20_2 = self.prom_20_2
        self.acc_20_2 = self.acc_20_2
        self.count_20_1 = self.count_20_1
        self.rank_20_1 = self.rank_20_1
        self.count_20_2 = self.count_20_2
        self.rank_20_2 = self.rank_20_2
        self.count_20_3 = self.count_20_3
        self.rank_20_3 = self.rank_20_3
        self.count_20_4 = self.count_20_4
        self.rank_20_4 = self.rank_20_4
        self.count_20_5 = self.count_20_5
        self.rank_20_5 = self.rank_20_5
        self.pv_has_21 = self.pv_has_21
        self.pv_21 = self.pv_21
        self.prom_has_21 = self.prom_has_21
        self.acc_has_21 = self.acc_has_21
        self.cand_has_21 = self.cand_has_21
        self.next_rank_21 = self.next_rank_21
        self.prom_21_0 = self.prom_21_0
        self.acc_21_0 = self.acc_21_0
        self.prom_21_1 = self.prom_21_1
        self.acc_21_1 = self.acc_21_1
        self.prom_21_2 = self.prom_21_2
        self.acc_21_2 = self.acc_21_2
        self.count_21_1 = self.count_21_1
        self.rank_21_1 = self.rank_21_1
        self.count_21_2 = self.count_21_2
        self.rank_21_2 = self.rank_21_2
        self.count_21_3 = self.count_21_3
        self.rank_21_3 = self.rank_21_3
        self.count_21_4 = self.count_21_4
        self.rank_21_4 = self.rank_21_4
        self.count_21_5 = self.count_21_5
        self.rank_21_5 = self.rank_21_5
        self.pv_has_22 = self.pv_has_22
        self.pv_22 = self.pv_22
        self.prom_has_22 = self.prom_has_22
        self.acc_has_22 = self.acc_has_22
        self.cand_has_22 = self.cand_has_22
        self.next_rank_22 = self.next_rank_22
        self.prom_22_0 = self.prom_22_0
        self.acc_22_0 = self.acc_22_0
        self.prom_22_1 = self.prom_22_1
        self.acc_22_1 = self.acc_22_1
        self.prom_22_2 = self.prom_22_2
        self.acc_22_2 = self.acc_22_2
        self.count_22_1 = self.count_22_1
        self.rank_22_1 = self.rank_22_1
        self.count_22_2 = self.count_22_2
        self.rank_22_2 = self.rank_22_2
        self.count_22_3 = self.count_22_3
        self.rank_22_3 = self.rank_22_3
        self.count_22_4 = self.count_22_4
        self.rank_22_4 = self.rank_22_4
        self.count_22_5 = self.count_22_5
        self.rank_22_5 = self.rank_22_5
        self.pv_has_23 = self.pv_has_23
        self.pv_23 = self.pv_23
        self.prom_has_23 = self.prom_has_23
        self.acc_has_23 = self.acc_has_23
        self.cand_has_23 = self.cand_has_23
        self.next_rank_23 = self.next_rank_23
        self.prom_23_0 = self.prom_23_0
        self.acc_23_0 = self.acc_23_0
        self.prom_23_1 = self.prom_23_1
        self.acc_23_1 = self.acc_23_1
        self.prom_23_2 = self.prom_23_2
        self.acc_23_2 = self.acc_23_2
        self.count_23_1 = self.count_23_1
        self.rank_23_1 = self.rank_23_1
        self.count_23_2 = self.count_23_2
        self.rank_23_2 = self.rank_23_2
        self.count_23_3 = self.count_23_3
        self.rank_23_3 = self.rank_23_3
        self.count_23_4 = self.count_23_4
        self.rank_23_4 = self.rank_23_4
        self.count_23_5 = self.count_23_5
        self.rank_23_5 = self.rank_23_5
        self.pv_has_24 = self.pv_has_24
        self.pv_24 = self.pv_24
        self.prom_has_24 = self.prom_has_24
        self.acc_has_24 = self.acc_has_24
        self.cand_has_24 = self.cand_has_24
        self.next_rank_24 = self.next_rank_24
        self.prom_24_0 = self.prom_24_0
        self.acc_24_0 = self.acc_24_0
        self.prom_24_1 = self.prom_24_1
        self.acc_24_1 = self.acc_24_1
        self.prom_24_2 = self.prom_24_2
        self.acc_24_2 = self.acc_24_2
        self.count_24_1 = self.count_24_1
        self.rank_24_1 = self.rank_24_1
        self.count_24_2 = self.count_24_2
        self.rank_24_2 = self.rank_24_2
        self.count_24_3 = self.count_24_3
        self.rank_24_3 = self.rank_24_3
        self.count_24_4 = self.count_24_4
        self.rank_24_4 = self.rank_24_4
        self.count_24_5 = self.count_24_5
        self.rank_24_5 = self.rank_24_5
        self.pv_has_25 = self.pv_has_25
        self.pv_25 = self.pv_25
        self.prom_has_25 = self.prom_has_25
        self.acc_has_25 = self.acc_has_25
        self.cand_has_25 = self.cand_has_25
        self.next_rank_25 = self.next_rank_25
        self.prom_25_0 = self.prom_25_0
        self.acc_25_0 = self.acc_25_0
        self.prom_25_1 = self.prom_25_1
        self.acc_25_1 = self.acc_25_1
        self.prom_25_2 = self.prom_25_2
        self.acc_25_2 = self.acc_25_2
        self.count_25_1 = self.count_25_1
        self.rank_25_1 = self.rank_25_1
        self.count_25_2 = self.count_25_2
        self.rank_25_2 = self.rank_25_2
        self.count_25_3 = self.count_25_3
        self.rank_25_3 = self.rank_25_3
        self.count_25_4 = self.count_25_4
        self.rank_25_4 = self.rank_25_4
        self.count_25_5 = self.count_25_5
        self.rank_25_5 = self.rank_25_5
        self.pv_has_26 = self.pv_has_26
        self.pv_26 = self.pv_26
        self.prom_has_26 = self.prom_has_26
        self.acc_has_26 = self.acc_has_26
        self.cand_has_26 = self.cand_has_26
        self.next_rank_26 = self.next_rank_26
        self.prom_26_0 = self.prom_26_0
        self.acc_26_0 = self.acc_26_0
        self.prom_26_1 = self.prom_26_1
        self.acc_26_1 = self.acc_26_1
        self.prom_26_2 = self.prom_26_2
        self.acc_26_2 = self.acc_26_2
        self.count_26_1 = self.count_26_1
        self.rank_26_1 = self.rank_26_1
        self.count_26_2 = self.count_26_2
        self.rank_26_2 = self.rank_26_2
        self.count_26_3 = self.count_26_3
        self.rank_26_3 = self.rank_26_3
        self.count_26_4 = self.count_26_4
        self.rank_26_4 = self.rank_26_4
        self.count_26_5 = self.count_26_5
        self.rank_26_5 = self.rank_26_5
        self.pv_has_27 = self.pv_has_27
        self.pv_27 = self.pv_27
        self.prom_has_27 = self.prom_has_27
        self.acc_has_27 = self.acc_has_27
        self.cand_has_27 = self.cand_has_27
        self.next_rank_27 = self.next_rank_27
        self.prom_27_0 = self.prom_27_0
        self.acc_27_0 = self.acc_27_0
        self.prom_27_1 = self.prom_27_1
        self.acc_27_1 = self.acc_27_1
        self.prom_27_2 = self.prom_27_2
        self.acc_27_2 = self.acc_27_2
        self.count_27_1 = self.count_27_1
        self.rank_27_1 = self.rank_27_1
        self.count_27_2 = self.count_27_2
        self.rank_27_2 = self.rank_27_2
        self.count_27_3 = self.count_27_3
        self.rank_27_3 = self.rank_27_3
        self.count_27_4 = self.count_27_4
        self.rank_27_4 = self.rank_27_4
        self.count_27_5 = self.count_27_5
        self.rank_27_5 = self.rank_27_5
        self.pv_has_28 = self.pv_has_28
        self.pv_28 = self.pv_28
        self.prom_has_28 = self.prom_has_28
        self.acc_has_28 = self.acc_has_28
        self.cand_has_28 = self.cand_has_28
        self.next_rank_28 = self.next_rank_28
        self.prom_28_0 = self.prom_28_0
        self.acc_28_0 = self.acc_28_0
        self.prom_28_1 = self.prom_28_1
        self.acc_28_1 = self.acc_28_1
        self.prom_28_2 = self.prom_28_2
        self.acc_28_2 = self.acc_28_2
        self.count_28_1 = self.count_28_1
        self.rank_28_1 = self.rank_28_1
        self.count_28_2 = self.count_28_2
        self.rank_28_2 = self.rank_28_2
        self.count_28_3 = self.count_28_3
        self.rank_28_3 = self.rank_28_3
        self.count_28_4 = self.count_28_4
        self.rank_28_4 = self.rank_28_4
        self.count_28_5 = self.count_28_5
        self.rank_28_5 = self.rank_28_5
        self.pv_has_29 = self.pv_has_29
        self.pv_29 = self.pv_29
        self.prom_has_29 = self.prom_has_29
        self.acc_has_29 = self.acc_has_29
        self.cand_has_29 = self.cand_has_29
        self.next_rank_29 = self.next_rank_29
        self.prom_29_0 = self.prom_29_0
        self.acc_29_0 = self.acc_29_0
        self.prom_29_1 = self.prom_29_1
        self.acc_29_1 = self.acc_29_1
        self.prom_29_2 = self.prom_29_2
        self.acc_29_2 = self.acc_29_2
        self.count_29_1 = self.count_29_1
        self.rank_29_1 = self.rank_29_1
        self.count_29_2 = self.count_29_2
        self.rank_29_2 = self.rank_29_2
        self.count_29_3 = self.count_29_3
        self.rank_29_3 = self.rank_29_3
        self.count_29_4 = self.count_29_4
        self.rank_29_4 = self.rank_29_4
        self.count_29_5 = self.count_29_5
        self.rank_29_5 = self.rank_29_5
        self.pv_has_30 = self.pv_has_30
        self.pv_30 = self.pv_30
        self.prom_has_30 = self.prom_has_30
        self.acc_has_30 = self.acc_has_30
        self.cand_has_30 = self.cand_has_30
        self.next_rank_30 = self.next_rank_30
        self.prom_30_0 = self.prom_30_0
        self.acc_30_0 = self.acc_30_0
        self.prom_30_1 = self.prom_30_1
        self.acc_30_1 = self.acc_30_1
        self.prom_30_2 = self.prom_30_2
        self.acc_30_2 = self.acc_30_2
        self.count_30_1 = self.count_30_1
        self.rank_30_1 = self.rank_30_1
        self.count_30_2 = self.count_30_2
        self.rank_30_2 = self.rank_30_2
        self.count_30_3 = self.count_30_3
        self.rank_30_3 = self.rank_30_3
        self.count_30_4 = self.count_30_4
        self.rank_30_4 = self.rank_30_4
        self.count_30_5 = self.count_30_5
        self.rank_30_5 = self.rank_30_5
        self.pv_has_31 = self.pv_has_31
        self.pv_31 = self.pv_31
        self.prom_has_31 = self.prom_has_31
        self.acc_has_31 = self.acc_has_31
        self.cand_has_31 = self.cand_has_31
        self.next_rank_31 = self.next_rank_31
        self.prom_31_0 = self.prom_31_0
        self.acc_31_0 = self.acc_31_0
        self.prom_31_1 = self.prom_31_1
        self.acc_31_1 = self.acc_31_1
        self.prom_31_2 = self.prom_31_2
        self.acc_31_2 = self.acc_31_2
        self.count_31_1 = self.count_31_1
        self.rank_31_1 = self.rank_31_1
        self.count_31_2 = self.count_31_2
        self.rank_31_2 = self.rank_31_2
        self.count_31_3 = self.count_31_3
        self.rank_31_3 = self.rank_31_3
        self.count_31_4 = self.count_31_4
        self.rank_31_4 = self.rank_31_4
        self.count_31_5 = self.count_31_5
        self.rank_31_5 = self.rank_31_5
        self.out_kind = 0
        self.declared = 0
        if self.status == 0:
            if self.pc != 0:
                if event == 3:
                    if self.pc == 2:
                        self.num = self.num + 1
                    elif self.pc == 3:
                        self.num = self.num + 2
                    self.pc = 0
            elif event == 1:
                if value != 0 and (self.own == 0 or self.own == value):
                    self.own = value
                    self.out_kind = 10
                    self.out_target = -1
                    self.out_num = self.num + 1
                    self.out_value = 0
                    self.out_prior_n = -1
                    self.out_prior_v = 0
                    self.pc = 2
            elif event == 2:
                if self.num >= 20 and self.accepted == 0:
                    if self.own != 0 and (self.own == 0 or self.own == self.own):
                        self.own = self.own
                        self.out_kind = 10
                        self.out_target = -1
                        self.out_num = self.num + 1
                        self.out_value = 0
                        self.out_prior_n = -1
                        self.out_prior_v = 0
                        self.pc = 3
                    else:
                        self.num = self.num + 1
                else:
                    self.num = self.num + 1
            elif event >= 10 and event <= 14:
                if number < self.num:
                    self.out_kind = 14
                    self.out_target = sender
                    self.out_num = self.num
                    self.out_value = 0
                    self.out_prior_n = -1
                    self.out_prior_v = 0
                    self.pc = 1
                elif event == 10:
                    self.num = max(self.num, number)
                    if number > self.promised:
                        self.promised = number
                        self.out_kind = 11
                        self.out_target = sender
                        self.out_num = self.promised
                        self.out_value = 0
                        self.out_prior_n = self.accepted_n
                        self.out_prior_v = self.accepted
                        self.pc = 1
                    else:
                        self.out_kind = 14
                        self.out_target = sender
                        self.out_num = self.num
                        self.out_value = 0
                        self.out_prior_n = -1
                        self.out_prior_v = 0
                        self.pc = 1
                elif event == 14:
                    self.num = max(self.num, number)
                elif event == 12:
                    self.num = max(self.num, number)
                    if self.accepted == 0 or self.accepted == value:
                        if number == 0:
                            self.pv_has_0 = 1
                            self.pv_0 = value
                        if number == 1:
                            self.pv_has_1 = 1
                            self.pv_1 = value
                        if number == 2:
                            self.pv_has_2 = 1
                            self.pv_2 = value
                        if number == 3:
                            self.pv_has_3 = 1
                            self.pv_3 = value
                        if number == 4:
                            self.pv_has_4 = 1
                            self.pv_4 = value
                        if number == 5:
                            self.pv_has_5 = 1
                            self.pv_5 = value
                        if number == 6:
                            self.pv_has_6 = 1
                            self.pv_6 = value
                        if number == 7:
                            self.pv_has_7 = 1
                            self.pv_7 = value
                        if number == 8:
                            self.pv_has_8 = 1
                            self.pv_8 = value
                        if number == 9:
                            self.pv_has_9 = 1
                            self.pv_9 = value
                        if number == 10:
                            self.pv_has_10 = 1
                            self.pv_10 = value
                        if number == 11:
                            self.pv_has_11 = 1
                            self.pv_11 = value
                        if number == 12:
                            self.pv_has_12 = 1
                            self.pv_12 = value
                        if number == 13:
                            self.pv_has_13 = 1
                            self.pv_13 = value
                        if number == 14:
                            self.pv_has_14 = 1
                            self.pv_14 = value
                        if number == 15:
                            self.pv_has_15 = 1
                            self.pv_15 = value
                        if number == 16:
                            self.pv_has_16 = 1
                            self.pv_16 = value
                        if number == 17:
                            self.pv_has_17 = 1
                            self.pv_17 = value
                        if number == 18:
                            self.pv_has_18 = 1
                            self.pv_18 = value
                        if number == 19:
                            self.pv_has_19 = 1
                            self.pv_19 = value
                        if number == 20:
                            self.pv_has_20 = 1
                            self.pv_20 = value
                        if number == 21:
                            self.pv_has_21 = 1
                            self.pv_21 = value
                        if number == 22:
                            self.pv_has_22 = 1
                            self.pv_22 = value
                        if number == 23:
                            self.pv_has_23 = 1
                            self.pv_23 = value
                        if number == 24:
                            self.pv_has_24 = 1
                            self.pv_24 = value
                        if number == 25:
                            self.pv_has_25 = 1
                            self.pv_25 = value
                        if number == 26:
                            self.pv_has_26 = 1
                            self.pv_26 = value
                        if number == 27:
                            self.pv_has_27 = 1
                            self.pv_27 = value
                        if number == 28:
                            self.pv_has_28 = 1
                            self.pv_28 = value
                        if number == 29:
                            self.pv_has_29 = 1
                            self.pv_29 = value
                        if number == 30:
                            self.pv_has_30 = 1
                            self.pv_30 = value
                        if number == 31:
                            self.pv_has_31 = 1
                            self.pv_31 = value
                        self.accepted = value
                        self.accepted_n = number
                        self.out_kind = 13
                        self.out_target = sender
                        self.out_num = number
                        self.out_value = value
                        self.out_prior_n = -1
                        self.out_prior_v = 0
                        self.pc = 1
                    else:
                        self.out_kind = 14
                        self.out_target = sender
                        self.out_num = self.num
                        self.out_value = 0
                        self.out_prior_n = -1
                        self.out_prior_v = 0
                        self.pc = 1
                elif event == 11:
                    present = self.num - self.num
                    if prior_value == 3:
                        present = self.cand_has_0
                    if prior_value == 4:
                        present = self.cand_has_1
                    if prior_value == 5:
                        present = self.cand_has_2
                    if number == 0:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_0 = 1
                                self.next_rank_0 = 0
                                self.count_0_1 = 0
                                self.rank_0_1 = 0
                                self.count_0_2 = 0
                                self.rank_0_2 = 0
                                self.count_0_3 = 0
                                self.rank_0_3 = 0
                                self.count_0_4 = 0
                                self.rank_0_4 = 0
                                self.count_0_5 = 0
                                self.rank_0_5 = 0
                            if self.cand_has_0 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_0_1 == 0:
                                        self.rank_0_1 = self.next_rank_0
                                        self.next_rank_0 = self.next_rank_0 + 1
                                    self.count_0_1 = self.count_0_1 + 1
                                if prior_value == 2:
                                    if self.count_0_2 == 0:
                                        self.rank_0_2 = self.next_rank_0
                                        self.next_rank_0 = self.next_rank_0 + 1
                                    self.count_0_2 = self.count_0_2 + 1
                                if prior_value == 3:
                                    if self.count_0_3 == 0:
                                        self.rank_0_3 = self.next_rank_0
                                        self.next_rank_0 = self.next_rank_0 + 1
                                    self.count_0_3 = self.count_0_3 + 1
                                if prior_value == 4:
                                    if self.count_0_4 == 0:
                                        self.rank_0_4 = self.next_rank_0
                                        self.next_rank_0 = self.next_rank_0 + 1
                                    self.count_0_4 = self.count_0_4 + 1
                                if prior_value == 5:
                                    if self.count_0_5 == 0:
                                        self.rank_0_5 = self.next_rank_0
                                        self.next_rank_0 = self.next_rank_0 + 1
                                    self.count_0_5 = self.count_0_5 + 1
                        if self.status == 0:
                            self.prom_has_0 = 1
                            if sender == 0:
                                self.prom_0_0 = 1
                            if sender == 1:
                                self.prom_0_1 = 1
                            if sender == 2:
                                self.prom_0_2 = 1
                            if self.prom_0_0 + self.prom_0_1 + self.prom_0_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_0 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_0_1 > best_count or (self.count_0_1 == best_count and self.count_0_1 != 0 and self.rank_0_1 < best_rank):
                                            best_count = self.count_0_1
                                            best_rank = self.rank_0_1
                                            choice = self.num - self.num + 1
                                        if self.count_0_2 > best_count or (self.count_0_2 == best_count and self.count_0_2 != 0 and self.rank_0_2 < best_rank):
                                            best_count = self.count_0_2
                                            best_rank = self.rank_0_2
                                            choice = self.num - self.num + 2
                                        if self.count_0_3 > best_count or (self.count_0_3 == best_count and self.count_0_3 != 0 and self.rank_0_3 < best_rank):
                                            best_count = self.count_0_3
                                            best_rank = self.rank_0_3
                                            choice = self.num - self.num + 3
                                        if self.count_0_4 > best_count or (self.count_0_4 == best_count and self.count_0_4 != 0 and self.rank_0_4 < best_rank):
                                            best_count = self.count_0_4
                                            best_rank = self.rank_0_4
                                            choice = self.num - self.num + 4
                                        if self.count_0_5 > best_count or (self.count_0_5 == best_count and self.count_0_5 != 0 and self.rank_0_5 < best_rank):
                                            best_count = self.count_0_5
                                            best_rank = self.rank_0_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_0 = 1
                                    self.pv_0 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 1:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_1 = 1
                                self.next_rank_1 = 0
                                self.count_1_1 = 0
                                self.rank_1_1 = 0
                                self.count_1_2 = 0
                                self.rank_1_2 = 0
                                self.count_1_3 = 0
                                self.rank_1_3 = 0
                                self.count_1_4 = 0
                                self.rank_1_4 = 0
                                self.count_1_5 = 0
                                self.rank_1_5 = 0
                            if self.cand_has_1 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_1_1 == 0:
                                        self.rank_1_1 = self.next_rank_1
                                        self.next_rank_1 = self.next_rank_1 + 1
                                    self.count_1_1 = self.count_1_1 + 1
                                if prior_value == 2:
                                    if self.count_1_2 == 0:
                                        self.rank_1_2 = self.next_rank_1
                                        self.next_rank_1 = self.next_rank_1 + 1
                                    self.count_1_2 = self.count_1_2 + 1
                                if prior_value == 3:
                                    if self.count_1_3 == 0:
                                        self.rank_1_3 = self.next_rank_1
                                        self.next_rank_1 = self.next_rank_1 + 1
                                    self.count_1_3 = self.count_1_3 + 1
                                if prior_value == 4:
                                    if self.count_1_4 == 0:
                                        self.rank_1_4 = self.next_rank_1
                                        self.next_rank_1 = self.next_rank_1 + 1
                                    self.count_1_4 = self.count_1_4 + 1
                                if prior_value == 5:
                                    if self.count_1_5 == 0:
                                        self.rank_1_5 = self.next_rank_1
                                        self.next_rank_1 = self.next_rank_1 + 1
                                    self.count_1_5 = self.count_1_5 + 1
                        if self.status == 0:
                            self.prom_has_1 = 1
                            if sender == 0:
                                self.prom_1_0 = 1
                            if sender == 1:
                                self.prom_1_1 = 1
                            if sender == 2:
                                self.prom_1_2 = 1
                            if self.prom_1_0 + self.prom_1_1 + self.prom_1_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_1 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_1_1 > best_count or (self.count_1_1 == best_count and self.count_1_1 != 0 and self.rank_1_1 < best_rank):
                                            best_count = self.count_1_1
                                            best_rank = self.rank_1_1
                                            choice = self.num - self.num + 1
                                        if self.count_1_2 > best_count or (self.count_1_2 == best_count and self.count_1_2 != 0 and self.rank_1_2 < best_rank):
                                            best_count = self.count_1_2
                                            best_rank = self.rank_1_2
                                            choice = self.num - self.num + 2
                                        if self.count_1_3 > best_count or (self.count_1_3 == best_count and self.count_1_3 != 0 and self.rank_1_3 < best_rank):
                                            best_count = self.count_1_3
                                            best_rank = self.rank_1_3
                                            choice = self.num - self.num + 3
                                        if self.count_1_4 > best_count or (self.count_1_4 == best_count and self.count_1_4 != 0 and self.rank_1_4 < best_rank):
                                            best_count = self.count_1_4
                                            best_rank = self.rank_1_4
                                            choice = self.num - self.num + 4
                                        if self.count_1_5 > best_count or (self.count_1_5 == best_count and self.count_1_5 != 0 and self.rank_1_5 < best_rank):
                                            best_count = self.count_1_5
                                            best_rank = self.rank_1_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_1 = 1
                                    self.pv_1 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 2:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_2 = 1
                                self.next_rank_2 = 0
                                self.count_2_1 = 0
                                self.rank_2_1 = 0
                                self.count_2_2 = 0
                                self.rank_2_2 = 0
                                self.count_2_3 = 0
                                self.rank_2_3 = 0
                                self.count_2_4 = 0
                                self.rank_2_4 = 0
                                self.count_2_5 = 0
                                self.rank_2_5 = 0
                            if self.cand_has_2 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_2_1 == 0:
                                        self.rank_2_1 = self.next_rank_2
                                        self.next_rank_2 = self.next_rank_2 + 1
                                    self.count_2_1 = self.count_2_1 + 1
                                if prior_value == 2:
                                    if self.count_2_2 == 0:
                                        self.rank_2_2 = self.next_rank_2
                                        self.next_rank_2 = self.next_rank_2 + 1
                                    self.count_2_2 = self.count_2_2 + 1
                                if prior_value == 3:
                                    if self.count_2_3 == 0:
                                        self.rank_2_3 = self.next_rank_2
                                        self.next_rank_2 = self.next_rank_2 + 1
                                    self.count_2_3 = self.count_2_3 + 1
                                if prior_value == 4:
                                    if self.count_2_4 == 0:
                                        self.rank_2_4 = self.next_rank_2
                                        self.next_rank_2 = self.next_rank_2 + 1
                                    self.count_2_4 = self.count_2_4 + 1
                                if prior_value == 5:
                                    if self.count_2_5 == 0:
                                        self.rank_2_5 = self.next_rank_2
                                        self.next_rank_2 = self.next_rank_2 + 1
                                    self.count_2_5 = self.count_2_5 + 1
                        if self.status == 0:
                            self.prom_has_2 = 1
                            if sender == 0:
                                self.prom_2_0 = 1
                            if sender == 1:
                                self.prom_2_1 = 1
                            if sender == 2:
                                self.prom_2_2 = 1
                            if self.prom_2_0 + self.prom_2_1 + self.prom_2_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_2 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_2_1 > best_count or (self.count_2_1 == best_count and self.count_2_1 != 0 and self.rank_2_1 < best_rank):
                                            best_count = self.count_2_1
                                            best_rank = self.rank_2_1
                                            choice = self.num - self.num + 1
                                        if self.count_2_2 > best_count or (self.count_2_2 == best_count and self.count_2_2 != 0 and self.rank_2_2 < best_rank):
                                            best_count = self.count_2_2
                                            best_rank = self.rank_2_2
                                            choice = self.num - self.num + 2
                                        if self.count_2_3 > best_count or (self.count_2_3 == best_count and self.count_2_3 != 0 and self.rank_2_3 < best_rank):
                                            best_count = self.count_2_3
                                            best_rank = self.rank_2_3
                                            choice = self.num - self.num + 3
                                        if self.count_2_4 > best_count or (self.count_2_4 == best_count and self.count_2_4 != 0 and self.rank_2_4 < best_rank):
                                            best_count = self.count_2_4
                                            best_rank = self.rank_2_4
                                            choice = self.num - self.num + 4
                                        if self.count_2_5 > best_count or (self.count_2_5 == best_count and self.count_2_5 != 0 and self.rank_2_5 < best_rank):
                                            best_count = self.count_2_5
                                            best_rank = self.rank_2_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_2 = 1
                                    self.pv_2 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 3:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_3 = 1
                                self.next_rank_3 = 0
                                self.count_3_1 = 0
                                self.rank_3_1 = 0
                                self.count_3_2 = 0
                                self.rank_3_2 = 0
                                self.count_3_3 = 0
                                self.rank_3_3 = 0
                                self.count_3_4 = 0
                                self.rank_3_4 = 0
                                self.count_3_5 = 0
                                self.rank_3_5 = 0
                            if self.cand_has_3 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_3_1 == 0:
                                        self.rank_3_1 = self.next_rank_3
                                        self.next_rank_3 = self.next_rank_3 + 1
                                    self.count_3_1 = self.count_3_1 + 1
                                if prior_value == 2:
                                    if self.count_3_2 == 0:
                                        self.rank_3_2 = self.next_rank_3
                                        self.next_rank_3 = self.next_rank_3 + 1
                                    self.count_3_2 = self.count_3_2 + 1
                                if prior_value == 3:
                                    if self.count_3_3 == 0:
                                        self.rank_3_3 = self.next_rank_3
                                        self.next_rank_3 = self.next_rank_3 + 1
                                    self.count_3_3 = self.count_3_3 + 1
                                if prior_value == 4:
                                    if self.count_3_4 == 0:
                                        self.rank_3_4 = self.next_rank_3
                                        self.next_rank_3 = self.next_rank_3 + 1
                                    self.count_3_4 = self.count_3_4 + 1
                                if prior_value == 5:
                                    if self.count_3_5 == 0:
                                        self.rank_3_5 = self.next_rank_3
                                        self.next_rank_3 = self.next_rank_3 + 1
                                    self.count_3_5 = self.count_3_5 + 1
                        if self.status == 0:
                            self.prom_has_3 = 1
                            if sender == 0:
                                self.prom_3_0 = 1
                            if sender == 1:
                                self.prom_3_1 = 1
                            if sender == 2:
                                self.prom_3_2 = 1
                            if self.prom_3_0 + self.prom_3_1 + self.prom_3_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_3 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_3_1 > best_count or (self.count_3_1 == best_count and self.count_3_1 != 0 and self.rank_3_1 < best_rank):
                                            best_count = self.count_3_1
                                            best_rank = self.rank_3_1
                                            choice = self.num - self.num + 1
                                        if self.count_3_2 > best_count or (self.count_3_2 == best_count and self.count_3_2 != 0 and self.rank_3_2 < best_rank):
                                            best_count = self.count_3_2
                                            best_rank = self.rank_3_2
                                            choice = self.num - self.num + 2
                                        if self.count_3_3 > best_count or (self.count_3_3 == best_count and self.count_3_3 != 0 and self.rank_3_3 < best_rank):
                                            best_count = self.count_3_3
                                            best_rank = self.rank_3_3
                                            choice = self.num - self.num + 3
                                        if self.count_3_4 > best_count or (self.count_3_4 == best_count and self.count_3_4 != 0 and self.rank_3_4 < best_rank):
                                            best_count = self.count_3_4
                                            best_rank = self.rank_3_4
                                            choice = self.num - self.num + 4
                                        if self.count_3_5 > best_count or (self.count_3_5 == best_count and self.count_3_5 != 0 and self.rank_3_5 < best_rank):
                                            best_count = self.count_3_5
                                            best_rank = self.rank_3_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_3 = 1
                                    self.pv_3 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 4:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_4 = 1
                                self.next_rank_4 = 0
                                self.count_4_1 = 0
                                self.rank_4_1 = 0
                                self.count_4_2 = 0
                                self.rank_4_2 = 0
                                self.count_4_3 = 0
                                self.rank_4_3 = 0
                                self.count_4_4 = 0
                                self.rank_4_4 = 0
                                self.count_4_5 = 0
                                self.rank_4_5 = 0
                            if self.cand_has_4 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_4_1 == 0:
                                        self.rank_4_1 = self.next_rank_4
                                        self.next_rank_4 = self.next_rank_4 + 1
                                    self.count_4_1 = self.count_4_1 + 1
                                if prior_value == 2:
                                    if self.count_4_2 == 0:
                                        self.rank_4_2 = self.next_rank_4
                                        self.next_rank_4 = self.next_rank_4 + 1
                                    self.count_4_2 = self.count_4_2 + 1
                                if prior_value == 3:
                                    if self.count_4_3 == 0:
                                        self.rank_4_3 = self.next_rank_4
                                        self.next_rank_4 = self.next_rank_4 + 1
                                    self.count_4_3 = self.count_4_3 + 1
                                if prior_value == 4:
                                    if self.count_4_4 == 0:
                                        self.rank_4_4 = self.next_rank_4
                                        self.next_rank_4 = self.next_rank_4 + 1
                                    self.count_4_4 = self.count_4_4 + 1
                                if prior_value == 5:
                                    if self.count_4_5 == 0:
                                        self.rank_4_5 = self.next_rank_4
                                        self.next_rank_4 = self.next_rank_4 + 1
                                    self.count_4_5 = self.count_4_5 + 1
                        if self.status == 0:
                            self.prom_has_4 = 1
                            if sender == 0:
                                self.prom_4_0 = 1
                            if sender == 1:
                                self.prom_4_1 = 1
                            if sender == 2:
                                self.prom_4_2 = 1
                            if self.prom_4_0 + self.prom_4_1 + self.prom_4_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_4 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_4_1 > best_count or (self.count_4_1 == best_count and self.count_4_1 != 0 and self.rank_4_1 < best_rank):
                                            best_count = self.count_4_1
                                            best_rank = self.rank_4_1
                                            choice = self.num - self.num + 1
                                        if self.count_4_2 > best_count or (self.count_4_2 == best_count and self.count_4_2 != 0 and self.rank_4_2 < best_rank):
                                            best_count = self.count_4_2
                                            best_rank = self.rank_4_2
                                            choice = self.num - self.num + 2
                                        if self.count_4_3 > best_count or (self.count_4_3 == best_count and self.count_4_3 != 0 and self.rank_4_3 < best_rank):
                                            best_count = self.count_4_3
                                            best_rank = self.rank_4_3
                                            choice = self.num - self.num + 3
                                        if self.count_4_4 > best_count or (self.count_4_4 == best_count and self.count_4_4 != 0 and self.rank_4_4 < best_rank):
                                            best_count = self.count_4_4
                                            best_rank = self.rank_4_4
                                            choice = self.num - self.num + 4
                                        if self.count_4_5 > best_count or (self.count_4_5 == best_count and self.count_4_5 != 0 and self.rank_4_5 < best_rank):
                                            best_count = self.count_4_5
                                            best_rank = self.rank_4_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_4 = 1
                                    self.pv_4 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 5:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_5 = 1
                                self.next_rank_5 = 0
                                self.count_5_1 = 0
                                self.rank_5_1 = 0
                                self.count_5_2 = 0
                                self.rank_5_2 = 0
                                self.count_5_3 = 0
                                self.rank_5_3 = 0
                                self.count_5_4 = 0
                                self.rank_5_4 = 0
                                self.count_5_5 = 0
                                self.rank_5_5 = 0
                            if self.cand_has_5 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_5_1 == 0:
                                        self.rank_5_1 = self.next_rank_5
                                        self.next_rank_5 = self.next_rank_5 + 1
                                    self.count_5_1 = self.count_5_1 + 1
                                if prior_value == 2:
                                    if self.count_5_2 == 0:
                                        self.rank_5_2 = self.next_rank_5
                                        self.next_rank_5 = self.next_rank_5 + 1
                                    self.count_5_2 = self.count_5_2 + 1
                                if prior_value == 3:
                                    if self.count_5_3 == 0:
                                        self.rank_5_3 = self.next_rank_5
                                        self.next_rank_5 = self.next_rank_5 + 1
                                    self.count_5_3 = self.count_5_3 + 1
                                if prior_value == 4:
                                    if self.count_5_4 == 0:
                                        self.rank_5_4 = self.next_rank_5
                                        self.next_rank_5 = self.next_rank_5 + 1
                                    self.count_5_4 = self.count_5_4 + 1
                                if prior_value == 5:
                                    if self.count_5_5 == 0:
                                        self.rank_5_5 = self.next_rank_5
                                        self.next_rank_5 = self.next_rank_5 + 1
                                    self.count_5_5 = self.count_5_5 + 1
                        if self.status == 0:
                            self.prom_has_5 = 1
                            if sender == 0:
                                self.prom_5_0 = 1
                            if sender == 1:
                                self.prom_5_1 = 1
                            if sender == 2:
                                self.prom_5_2 = 1
                            if self.prom_5_0 + self.prom_5_1 + self.prom_5_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_5 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_5_1 > best_count or (self.count_5_1 == best_count and self.count_5_1 != 0 and self.rank_5_1 < best_rank):
                                            best_count = self.count_5_1
                                            best_rank = self.rank_5_1
                                            choice = self.num - self.num + 1
                                        if self.count_5_2 > best_count or (self.count_5_2 == best_count and self.count_5_2 != 0 and self.rank_5_2 < best_rank):
                                            best_count = self.count_5_2
                                            best_rank = self.rank_5_2
                                            choice = self.num - self.num + 2
                                        if self.count_5_3 > best_count or (self.count_5_3 == best_count and self.count_5_3 != 0 and self.rank_5_3 < best_rank):
                                            best_count = self.count_5_3
                                            best_rank = self.rank_5_3
                                            choice = self.num - self.num + 3
                                        if self.count_5_4 > best_count or (self.count_5_4 == best_count and self.count_5_4 != 0 and self.rank_5_4 < best_rank):
                                            best_count = self.count_5_4
                                            best_rank = self.rank_5_4
                                            choice = self.num - self.num + 4
                                        if self.count_5_5 > best_count or (self.count_5_5 == best_count and self.count_5_5 != 0 and self.rank_5_5 < best_rank):
                                            best_count = self.count_5_5
                                            best_rank = self.rank_5_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_5 = 1
                                    self.pv_5 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 6:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_6 = 1
                                self.next_rank_6 = 0
                                self.count_6_1 = 0
                                self.rank_6_1 = 0
                                self.count_6_2 = 0
                                self.rank_6_2 = 0
                                self.count_6_3 = 0
                                self.rank_6_3 = 0
                                self.count_6_4 = 0
                                self.rank_6_4 = 0
                                self.count_6_5 = 0
                                self.rank_6_5 = 0
                            if self.cand_has_6 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_6_1 == 0:
                                        self.rank_6_1 = self.next_rank_6
                                        self.next_rank_6 = self.next_rank_6 + 1
                                    self.count_6_1 = self.count_6_1 + 1
                                if prior_value == 2:
                                    if self.count_6_2 == 0:
                                        self.rank_6_2 = self.next_rank_6
                                        self.next_rank_6 = self.next_rank_6 + 1
                                    self.count_6_2 = self.count_6_2 + 1
                                if prior_value == 3:
                                    if self.count_6_3 == 0:
                                        self.rank_6_3 = self.next_rank_6
                                        self.next_rank_6 = self.next_rank_6 + 1
                                    self.count_6_3 = self.count_6_3 + 1
                                if prior_value == 4:
                                    if self.count_6_4 == 0:
                                        self.rank_6_4 = self.next_rank_6
                                        self.next_rank_6 = self.next_rank_6 + 1
                                    self.count_6_4 = self.count_6_4 + 1
                                if prior_value == 5:
                                    if self.count_6_5 == 0:
                                        self.rank_6_5 = self.next_rank_6
                                        self.next_rank_6 = self.next_rank_6 + 1
                                    self.count_6_5 = self.count_6_5 + 1
                        if self.status == 0:
                            self.prom_has_6 = 1
                            if sender == 0:
                                self.prom_6_0 = 1
                            if sender == 1:
                                self.prom_6_1 = 1
                            if sender == 2:
                                self.prom_6_2 = 1
                            if self.prom_6_0 + self.prom_6_1 + self.prom_6_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_6 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_6_1 > best_count or (self.count_6_1 == best_count and self.count_6_1 != 0 and self.rank_6_1 < best_rank):
                                            best_count = self.count_6_1
                                            best_rank = self.rank_6_1
                                            choice = self.num - self.num + 1
                                        if self.count_6_2 > best_count or (self.count_6_2 == best_count and self.count_6_2 != 0 and self.rank_6_2 < best_rank):
                                            best_count = self.count_6_2
                                            best_rank = self.rank_6_2
                                            choice = self.num - self.num + 2
                                        if self.count_6_3 > best_count or (self.count_6_3 == best_count and self.count_6_3 != 0 and self.rank_6_3 < best_rank):
                                            best_count = self.count_6_3
                                            best_rank = self.rank_6_3
                                            choice = self.num - self.num + 3
                                        if self.count_6_4 > best_count or (self.count_6_4 == best_count and self.count_6_4 != 0 and self.rank_6_4 < best_rank):
                                            best_count = self.count_6_4
                                            best_rank = self.rank_6_4
                                            choice = self.num - self.num + 4
                                        if self.count_6_5 > best_count or (self.count_6_5 == best_count and self.count_6_5 != 0 and self.rank_6_5 < best_rank):
                                            best_count = self.count_6_5
                                            best_rank = self.rank_6_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_6 = 1
                                    self.pv_6 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 7:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_7 = 1
                                self.next_rank_7 = 0
                                self.count_7_1 = 0
                                self.rank_7_1 = 0
                                self.count_7_2 = 0
                                self.rank_7_2 = 0
                                self.count_7_3 = 0
                                self.rank_7_3 = 0
                                self.count_7_4 = 0
                                self.rank_7_4 = 0
                                self.count_7_5 = 0
                                self.rank_7_5 = 0
                            if self.cand_has_7 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_7_1 == 0:
                                        self.rank_7_1 = self.next_rank_7
                                        self.next_rank_7 = self.next_rank_7 + 1
                                    self.count_7_1 = self.count_7_1 + 1
                                if prior_value == 2:
                                    if self.count_7_2 == 0:
                                        self.rank_7_2 = self.next_rank_7
                                        self.next_rank_7 = self.next_rank_7 + 1
                                    self.count_7_2 = self.count_7_2 + 1
                                if prior_value == 3:
                                    if self.count_7_3 == 0:
                                        self.rank_7_3 = self.next_rank_7
                                        self.next_rank_7 = self.next_rank_7 + 1
                                    self.count_7_3 = self.count_7_3 + 1
                                if prior_value == 4:
                                    if self.count_7_4 == 0:
                                        self.rank_7_4 = self.next_rank_7
                                        self.next_rank_7 = self.next_rank_7 + 1
                                    self.count_7_4 = self.count_7_4 + 1
                                if prior_value == 5:
                                    if self.count_7_5 == 0:
                                        self.rank_7_5 = self.next_rank_7
                                        self.next_rank_7 = self.next_rank_7 + 1
                                    self.count_7_5 = self.count_7_5 + 1
                        if self.status == 0:
                            self.prom_has_7 = 1
                            if sender == 0:
                                self.prom_7_0 = 1
                            if sender == 1:
                                self.prom_7_1 = 1
                            if sender == 2:
                                self.prom_7_2 = 1
                            if self.prom_7_0 + self.prom_7_1 + self.prom_7_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_7 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_7_1 > best_count or (self.count_7_1 == best_count and self.count_7_1 != 0 and self.rank_7_1 < best_rank):
                                            best_count = self.count_7_1
                                            best_rank = self.rank_7_1
                                            choice = self.num - self.num + 1
                                        if self.count_7_2 > best_count or (self.count_7_2 == best_count and self.count_7_2 != 0 and self.rank_7_2 < best_rank):
                                            best_count = self.count_7_2
                                            best_rank = self.rank_7_2
                                            choice = self.num - self.num + 2
                                        if self.count_7_3 > best_count or (self.count_7_3 == best_count and self.count_7_3 != 0 and self.rank_7_3 < best_rank):
                                            best_count = self.count_7_3
                                            best_rank = self.rank_7_3
                                            choice = self.num - self.num + 3
                                        if self.count_7_4 > best_count or (self.count_7_4 == best_count and self.count_7_4 != 0 and self.rank_7_4 < best_rank):
                                            best_count = self.count_7_4
                                            best_rank = self.rank_7_4
                                            choice = self.num - self.num + 4
                                        if self.count_7_5 > best_count or (self.count_7_5 == best_count and self.count_7_5 != 0 and self.rank_7_5 < best_rank):
                                            best_count = self.count_7_5
                                            best_rank = self.rank_7_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_7 = 1
                                    self.pv_7 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 8:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_8 = 1
                                self.next_rank_8 = 0
                                self.count_8_1 = 0
                                self.rank_8_1 = 0
                                self.count_8_2 = 0
                                self.rank_8_2 = 0
                                self.count_8_3 = 0
                                self.rank_8_3 = 0
                                self.count_8_4 = 0
                                self.rank_8_4 = 0
                                self.count_8_5 = 0
                                self.rank_8_5 = 0
                            if self.cand_has_8 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_8_1 == 0:
                                        self.rank_8_1 = self.next_rank_8
                                        self.next_rank_8 = self.next_rank_8 + 1
                                    self.count_8_1 = self.count_8_1 + 1
                                if prior_value == 2:
                                    if self.count_8_2 == 0:
                                        self.rank_8_2 = self.next_rank_8
                                        self.next_rank_8 = self.next_rank_8 + 1
                                    self.count_8_2 = self.count_8_2 + 1
                                if prior_value == 3:
                                    if self.count_8_3 == 0:
                                        self.rank_8_3 = self.next_rank_8
                                        self.next_rank_8 = self.next_rank_8 + 1
                                    self.count_8_3 = self.count_8_3 + 1
                                if prior_value == 4:
                                    if self.count_8_4 == 0:
                                        self.rank_8_4 = self.next_rank_8
                                        self.next_rank_8 = self.next_rank_8 + 1
                                    self.count_8_4 = self.count_8_4 + 1
                                if prior_value == 5:
                                    if self.count_8_5 == 0:
                                        self.rank_8_5 = self.next_rank_8
                                        self.next_rank_8 = self.next_rank_8 + 1
                                    self.count_8_5 = self.count_8_5 + 1
                        if self.status == 0:
                            self.prom_has_8 = 1
                            if sender == 0:
                                self.prom_8_0 = 1
                            if sender == 1:
                                self.prom_8_1 = 1
                            if sender == 2:
                                self.prom_8_2 = 1
                            if self.prom_8_0 + self.prom_8_1 + self.prom_8_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_8 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_8_1 > best_count or (self.count_8_1 == best_count and self.count_8_1 != 0 and self.rank_8_1 < best_rank):
                                            best_count = self.count_8_1
                                            best_rank = self.rank_8_1
                                            choice = self.num - self.num + 1
                                        if self.count_8_2 > best_count or (self.count_8_2 == best_count and self.count_8_2 != 0 and self.rank_8_2 < best_rank):
                                            best_count = self.count_8_2
                                            best_rank = self.rank_8_2
                                            choice = self.num - self.num + 2
                                        if self.count_8_3 > best_count or (self.count_8_3 == best_count and self.count_8_3 != 0 and self.rank_8_3 < best_rank):
                                            best_count = self.count_8_3
                                            best_rank = self.rank_8_3
                                            choice = self.num - self.num + 3
                                        if self.count_8_4 > best_count or (self.count_8_4 == best_count and self.count_8_4 != 0 and self.rank_8_4 < best_rank):
                                            best_count = self.count_8_4
                                            best_rank = self.rank_8_4
                                            choice = self.num - self.num + 4
                                        if self.count_8_5 > best_count or (self.count_8_5 == best_count and self.count_8_5 != 0 and self.rank_8_5 < best_rank):
                                            best_count = self.count_8_5
                                            best_rank = self.rank_8_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_8 = 1
                                    self.pv_8 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 9:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_9 = 1
                                self.next_rank_9 = 0
                                self.count_9_1 = 0
                                self.rank_9_1 = 0
                                self.count_9_2 = 0
                                self.rank_9_2 = 0
                                self.count_9_3 = 0
                                self.rank_9_3 = 0
                                self.count_9_4 = 0
                                self.rank_9_4 = 0
                                self.count_9_5 = 0
                                self.rank_9_5 = 0
                            if self.cand_has_9 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_9_1 == 0:
                                        self.rank_9_1 = self.next_rank_9
                                        self.next_rank_9 = self.next_rank_9 + 1
                                    self.count_9_1 = self.count_9_1 + 1
                                if prior_value == 2:
                                    if self.count_9_2 == 0:
                                        self.rank_9_2 = self.next_rank_9
                                        self.next_rank_9 = self.next_rank_9 + 1
                                    self.count_9_2 = self.count_9_2 + 1
                                if prior_value == 3:
                                    if self.count_9_3 == 0:
                                        self.rank_9_3 = self.next_rank_9
                                        self.next_rank_9 = self.next_rank_9 + 1
                                    self.count_9_3 = self.count_9_3 + 1
                                if prior_value == 4:
                                    if self.count_9_4 == 0:
                                        self.rank_9_4 = self.next_rank_9
                                        self.next_rank_9 = self.next_rank_9 + 1
                                    self.count_9_4 = self.count_9_4 + 1
                                if prior_value == 5:
                                    if self.count_9_5 == 0:
                                        self.rank_9_5 = self.next_rank_9
                                        self.next_rank_9 = self.next_rank_9 + 1
                                    self.count_9_5 = self.count_9_5 + 1
                        if self.status == 0:
                            self.prom_has_9 = 1
                            if sender == 0:
                                self.prom_9_0 = 1
                            if sender == 1:
                                self.prom_9_1 = 1
                            if sender == 2:
                                self.prom_9_2 = 1
                            if self.prom_9_0 + self.prom_9_1 + self.prom_9_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_9 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_9_1 > best_count or (self.count_9_1 == best_count and self.count_9_1 != 0 and self.rank_9_1 < best_rank):
                                            best_count = self.count_9_1
                                            best_rank = self.rank_9_1
                                            choice = self.num - self.num + 1
                                        if self.count_9_2 > best_count or (self.count_9_2 == best_count and self.count_9_2 != 0 and self.rank_9_2 < best_rank):
                                            best_count = self.count_9_2
                                            best_rank = self.rank_9_2
                                            choice = self.num - self.num + 2
                                        if self.count_9_3 > best_count or (self.count_9_3 == best_count and self.count_9_3 != 0 and self.rank_9_3 < best_rank):
                                            best_count = self.count_9_3
                                            best_rank = self.rank_9_3
                                            choice = self.num - self.num + 3
                                        if self.count_9_4 > best_count or (self.count_9_4 == best_count and self.count_9_4 != 0 and self.rank_9_4 < best_rank):
                                            best_count = self.count_9_4
                                            best_rank = self.rank_9_4
                                            choice = self.num - self.num + 4
                                        if self.count_9_5 > best_count or (self.count_9_5 == best_count and self.count_9_5 != 0 and self.rank_9_5 < best_rank):
                                            best_count = self.count_9_5
                                            best_rank = self.rank_9_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_9 = 1
                                    self.pv_9 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 10:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_10 = 1
                                self.next_rank_10 = 0
                                self.count_10_1 = 0
                                self.rank_10_1 = 0
                                self.count_10_2 = 0
                                self.rank_10_2 = 0
                                self.count_10_3 = 0
                                self.rank_10_3 = 0
                                self.count_10_4 = 0
                                self.rank_10_4 = 0
                                self.count_10_5 = 0
                                self.rank_10_5 = 0
                            if self.cand_has_10 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_10_1 == 0:
                                        self.rank_10_1 = self.next_rank_10
                                        self.next_rank_10 = self.next_rank_10 + 1
                                    self.count_10_1 = self.count_10_1 + 1
                                if prior_value == 2:
                                    if self.count_10_2 == 0:
                                        self.rank_10_2 = self.next_rank_10
                                        self.next_rank_10 = self.next_rank_10 + 1
                                    self.count_10_2 = self.count_10_2 + 1
                                if prior_value == 3:
                                    if self.count_10_3 == 0:
                                        self.rank_10_3 = self.next_rank_10
                                        self.next_rank_10 = self.next_rank_10 + 1
                                    self.count_10_3 = self.count_10_3 + 1
                                if prior_value == 4:
                                    if self.count_10_4 == 0:
                                        self.rank_10_4 = self.next_rank_10
                                        self.next_rank_10 = self.next_rank_10 + 1
                                    self.count_10_4 = self.count_10_4 + 1
                                if prior_value == 5:
                                    if self.count_10_5 == 0:
                                        self.rank_10_5 = self.next_rank_10
                                        self.next_rank_10 = self.next_rank_10 + 1
                                    self.count_10_5 = self.count_10_5 + 1
                        if self.status == 0:
                            self.prom_has_10 = 1
                            if sender == 0:
                                self.prom_10_0 = 1
                            if sender == 1:
                                self.prom_10_1 = 1
                            if sender == 2:
                                self.prom_10_2 = 1
                            if self.prom_10_0 + self.prom_10_1 + self.prom_10_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_10 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_10_1 > best_count or (self.count_10_1 == best_count and self.count_10_1 != 0 and self.rank_10_1 < best_rank):
                                            best_count = self.count_10_1
                                            best_rank = self.rank_10_1
                                            choice = self.num - self.num + 1
                                        if self.count_10_2 > best_count or (self.count_10_2 == best_count and self.count_10_2 != 0 and self.rank_10_2 < best_rank):
                                            best_count = self.count_10_2
                                            best_rank = self.rank_10_2
                                            choice = self.num - self.num + 2
                                        if self.count_10_3 > best_count or (self.count_10_3 == best_count and self.count_10_3 != 0 and self.rank_10_3 < best_rank):
                                            best_count = self.count_10_3
                                            best_rank = self.rank_10_3
                                            choice = self.num - self.num + 3
                                        if self.count_10_4 > best_count or (self.count_10_4 == best_count and self.count_10_4 != 0 and self.rank_10_4 < best_rank):
                                            best_count = self.count_10_4
                                            best_rank = self.rank_10_4
                                            choice = self.num - self.num + 4
                                        if self.count_10_5 > best_count or (self.count_10_5 == best_count and self.count_10_5 != 0 and self.rank_10_5 < best_rank):
                                            best_count = self.count_10_5
                                            best_rank = self.rank_10_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_10 = 1
                                    self.pv_10 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 11:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_11 = 1
                                self.next_rank_11 = 0
                                self.count_11_1 = 0
                                self.rank_11_1 = 0
                                self.count_11_2 = 0
                                self.rank_11_2 = 0
                                self.count_11_3 = 0
                                self.rank_11_3 = 0
                                self.count_11_4 = 0
                                self.rank_11_4 = 0
                                self.count_11_5 = 0
                                self.rank_11_5 = 0
                            if self.cand_has_11 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_11_1 == 0:
                                        self.rank_11_1 = self.next_rank_11
                                        self.next_rank_11 = self.next_rank_11 + 1
                                    self.count_11_1 = self.count_11_1 + 1
                                if prior_value == 2:
                                    if self.count_11_2 == 0:
                                        self.rank_11_2 = self.next_rank_11
                                        self.next_rank_11 = self.next_rank_11 + 1
                                    self.count_11_2 = self.count_11_2 + 1
                                if prior_value == 3:
                                    if self.count_11_3 == 0:
                                        self.rank_11_3 = self.next_rank_11
                                        self.next_rank_11 = self.next_rank_11 + 1
                                    self.count_11_3 = self.count_11_3 + 1
                                if prior_value == 4:
                                    if self.count_11_4 == 0:
                                        self.rank_11_4 = self.next_rank_11
                                        self.next_rank_11 = self.next_rank_11 + 1
                                    self.count_11_4 = self.count_11_4 + 1
                                if prior_value == 5:
                                    if self.count_11_5 == 0:
                                        self.rank_11_5 = self.next_rank_11
                                        self.next_rank_11 = self.next_rank_11 + 1
                                    self.count_11_5 = self.count_11_5 + 1
                        if self.status == 0:
                            self.prom_has_11 = 1
                            if sender == 0:
                                self.prom_11_0 = 1
                            if sender == 1:
                                self.prom_11_1 = 1
                            if sender == 2:
                                self.prom_11_2 = 1
                            if self.prom_11_0 + self.prom_11_1 + self.prom_11_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_11 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_11_1 > best_count or (self.count_11_1 == best_count and self.count_11_1 != 0 and self.rank_11_1 < best_rank):
                                            best_count = self.count_11_1
                                            best_rank = self.rank_11_1
                                            choice = self.num - self.num + 1
                                        if self.count_11_2 > best_count or (self.count_11_2 == best_count and self.count_11_2 != 0 and self.rank_11_2 < best_rank):
                                            best_count = self.count_11_2
                                            best_rank = self.rank_11_2
                                            choice = self.num - self.num + 2
                                        if self.count_11_3 > best_count or (self.count_11_3 == best_count and self.count_11_3 != 0 and self.rank_11_3 < best_rank):
                                            best_count = self.count_11_3
                                            best_rank = self.rank_11_3
                                            choice = self.num - self.num + 3
                                        if self.count_11_4 > best_count or (self.count_11_4 == best_count and self.count_11_4 != 0 and self.rank_11_4 < best_rank):
                                            best_count = self.count_11_4
                                            best_rank = self.rank_11_4
                                            choice = self.num - self.num + 4
                                        if self.count_11_5 > best_count or (self.count_11_5 == best_count and self.count_11_5 != 0 and self.rank_11_5 < best_rank):
                                            best_count = self.count_11_5
                                            best_rank = self.rank_11_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_11 = 1
                                    self.pv_11 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 12:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_12 = 1
                                self.next_rank_12 = 0
                                self.count_12_1 = 0
                                self.rank_12_1 = 0
                                self.count_12_2 = 0
                                self.rank_12_2 = 0
                                self.count_12_3 = 0
                                self.rank_12_3 = 0
                                self.count_12_4 = 0
                                self.rank_12_4 = 0
                                self.count_12_5 = 0
                                self.rank_12_5 = 0
                            if self.cand_has_12 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_12_1 == 0:
                                        self.rank_12_1 = self.next_rank_12
                                        self.next_rank_12 = self.next_rank_12 + 1
                                    self.count_12_1 = self.count_12_1 + 1
                                if prior_value == 2:
                                    if self.count_12_2 == 0:
                                        self.rank_12_2 = self.next_rank_12
                                        self.next_rank_12 = self.next_rank_12 + 1
                                    self.count_12_2 = self.count_12_2 + 1
                                if prior_value == 3:
                                    if self.count_12_3 == 0:
                                        self.rank_12_3 = self.next_rank_12
                                        self.next_rank_12 = self.next_rank_12 + 1
                                    self.count_12_3 = self.count_12_3 + 1
                                if prior_value == 4:
                                    if self.count_12_4 == 0:
                                        self.rank_12_4 = self.next_rank_12
                                        self.next_rank_12 = self.next_rank_12 + 1
                                    self.count_12_4 = self.count_12_4 + 1
                                if prior_value == 5:
                                    if self.count_12_5 == 0:
                                        self.rank_12_5 = self.next_rank_12
                                        self.next_rank_12 = self.next_rank_12 + 1
                                    self.count_12_5 = self.count_12_5 + 1
                        if self.status == 0:
                            self.prom_has_12 = 1
                            if sender == 0:
                                self.prom_12_0 = 1
                            if sender == 1:
                                self.prom_12_1 = 1
                            if sender == 2:
                                self.prom_12_2 = 1
                            if self.prom_12_0 + self.prom_12_1 + self.prom_12_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_12 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_12_1 > best_count or (self.count_12_1 == best_count and self.count_12_1 != 0 and self.rank_12_1 < best_rank):
                                            best_count = self.count_12_1
                                            best_rank = self.rank_12_1
                                            choice = self.num - self.num + 1
                                        if self.count_12_2 > best_count or (self.count_12_2 == best_count and self.count_12_2 != 0 and self.rank_12_2 < best_rank):
                                            best_count = self.count_12_2
                                            best_rank = self.rank_12_2
                                            choice = self.num - self.num + 2
                                        if self.count_12_3 > best_count or (self.count_12_3 == best_count and self.count_12_3 != 0 and self.rank_12_3 < best_rank):
                                            best_count = self.count_12_3
                                            best_rank = self.rank_12_3
                                            choice = self.num - self.num + 3
                                        if self.count_12_4 > best_count or (self.count_12_4 == best_count and self.count_12_4 != 0 and self.rank_12_4 < best_rank):
                                            best_count = self.count_12_4
                                            best_rank = self.rank_12_4
                                            choice = self.num - self.num + 4
                                        if self.count_12_5 > best_count or (self.count_12_5 == best_count and self.count_12_5 != 0 and self.rank_12_5 < best_rank):
                                            best_count = self.count_12_5
                                            best_rank = self.rank_12_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_12 = 1
                                    self.pv_12 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 13:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_13 = 1
                                self.next_rank_13 = 0
                                self.count_13_1 = 0
                                self.rank_13_1 = 0
                                self.count_13_2 = 0
                                self.rank_13_2 = 0
                                self.count_13_3 = 0
                                self.rank_13_3 = 0
                                self.count_13_4 = 0
                                self.rank_13_4 = 0
                                self.count_13_5 = 0
                                self.rank_13_5 = 0
                            if self.cand_has_13 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_13_1 == 0:
                                        self.rank_13_1 = self.next_rank_13
                                        self.next_rank_13 = self.next_rank_13 + 1
                                    self.count_13_1 = self.count_13_1 + 1
                                if prior_value == 2:
                                    if self.count_13_2 == 0:
                                        self.rank_13_2 = self.next_rank_13
                                        self.next_rank_13 = self.next_rank_13 + 1
                                    self.count_13_2 = self.count_13_2 + 1
                                if prior_value == 3:
                                    if self.count_13_3 == 0:
                                        self.rank_13_3 = self.next_rank_13
                                        self.next_rank_13 = self.next_rank_13 + 1
                                    self.count_13_3 = self.count_13_3 + 1
                                if prior_value == 4:
                                    if self.count_13_4 == 0:
                                        self.rank_13_4 = self.next_rank_13
                                        self.next_rank_13 = self.next_rank_13 + 1
                                    self.count_13_4 = self.count_13_4 + 1
                                if prior_value == 5:
                                    if self.count_13_5 == 0:
                                        self.rank_13_5 = self.next_rank_13
                                        self.next_rank_13 = self.next_rank_13 + 1
                                    self.count_13_5 = self.count_13_5 + 1
                        if self.status == 0:
                            self.prom_has_13 = 1
                            if sender == 0:
                                self.prom_13_0 = 1
                            if sender == 1:
                                self.prom_13_1 = 1
                            if sender == 2:
                                self.prom_13_2 = 1
                            if self.prom_13_0 + self.prom_13_1 + self.prom_13_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_13 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_13_1 > best_count or (self.count_13_1 == best_count and self.count_13_1 != 0 and self.rank_13_1 < best_rank):
                                            best_count = self.count_13_1
                                            best_rank = self.rank_13_1
                                            choice = self.num - self.num + 1
                                        if self.count_13_2 > best_count or (self.count_13_2 == best_count and self.count_13_2 != 0 and self.rank_13_2 < best_rank):
                                            best_count = self.count_13_2
                                            best_rank = self.rank_13_2
                                            choice = self.num - self.num + 2
                                        if self.count_13_3 > best_count or (self.count_13_3 == best_count and self.count_13_3 != 0 and self.rank_13_3 < best_rank):
                                            best_count = self.count_13_3
                                            best_rank = self.rank_13_3
                                            choice = self.num - self.num + 3
                                        if self.count_13_4 > best_count or (self.count_13_4 == best_count and self.count_13_4 != 0 and self.rank_13_4 < best_rank):
                                            best_count = self.count_13_4
                                            best_rank = self.rank_13_4
                                            choice = self.num - self.num + 4
                                        if self.count_13_5 > best_count or (self.count_13_5 == best_count and self.count_13_5 != 0 and self.rank_13_5 < best_rank):
                                            best_count = self.count_13_5
                                            best_rank = self.rank_13_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_13 = 1
                                    self.pv_13 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 14:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_14 = 1
                                self.next_rank_14 = 0
                                self.count_14_1 = 0
                                self.rank_14_1 = 0
                                self.count_14_2 = 0
                                self.rank_14_2 = 0
                                self.count_14_3 = 0
                                self.rank_14_3 = 0
                                self.count_14_4 = 0
                                self.rank_14_4 = 0
                                self.count_14_5 = 0
                                self.rank_14_5 = 0
                            if self.cand_has_14 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_14_1 == 0:
                                        self.rank_14_1 = self.next_rank_14
                                        self.next_rank_14 = self.next_rank_14 + 1
                                    self.count_14_1 = self.count_14_1 + 1
                                if prior_value == 2:
                                    if self.count_14_2 == 0:
                                        self.rank_14_2 = self.next_rank_14
                                        self.next_rank_14 = self.next_rank_14 + 1
                                    self.count_14_2 = self.count_14_2 + 1
                                if prior_value == 3:
                                    if self.count_14_3 == 0:
                                        self.rank_14_3 = self.next_rank_14
                                        self.next_rank_14 = self.next_rank_14 + 1
                                    self.count_14_3 = self.count_14_3 + 1
                                if prior_value == 4:
                                    if self.count_14_4 == 0:
                                        self.rank_14_4 = self.next_rank_14
                                        self.next_rank_14 = self.next_rank_14 + 1
                                    self.count_14_4 = self.count_14_4 + 1
                                if prior_value == 5:
                                    if self.count_14_5 == 0:
                                        self.rank_14_5 = self.next_rank_14
                                        self.next_rank_14 = self.next_rank_14 + 1
                                    self.count_14_5 = self.count_14_5 + 1
                        if self.status == 0:
                            self.prom_has_14 = 1
                            if sender == 0:
                                self.prom_14_0 = 1
                            if sender == 1:
                                self.prom_14_1 = 1
                            if sender == 2:
                                self.prom_14_2 = 1
                            if self.prom_14_0 + self.prom_14_1 + self.prom_14_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_14 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_14_1 > best_count or (self.count_14_1 == best_count and self.count_14_1 != 0 and self.rank_14_1 < best_rank):
                                            best_count = self.count_14_1
                                            best_rank = self.rank_14_1
                                            choice = self.num - self.num + 1
                                        if self.count_14_2 > best_count or (self.count_14_2 == best_count and self.count_14_2 != 0 and self.rank_14_2 < best_rank):
                                            best_count = self.count_14_2
                                            best_rank = self.rank_14_2
                                            choice = self.num - self.num + 2
                                        if self.count_14_3 > best_count or (self.count_14_3 == best_count and self.count_14_3 != 0 and self.rank_14_3 < best_rank):
                                            best_count = self.count_14_3
                                            best_rank = self.rank_14_3
                                            choice = self.num - self.num + 3
                                        if self.count_14_4 > best_count or (self.count_14_4 == best_count and self.count_14_4 != 0 and self.rank_14_4 < best_rank):
                                            best_count = self.count_14_4
                                            best_rank = self.rank_14_4
                                            choice = self.num - self.num + 4
                                        if self.count_14_5 > best_count or (self.count_14_5 == best_count and self.count_14_5 != 0 and self.rank_14_5 < best_rank):
                                            best_count = self.count_14_5
                                            best_rank = self.rank_14_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_14 = 1
                                    self.pv_14 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 15:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_15 = 1
                                self.next_rank_15 = 0
                                self.count_15_1 = 0
                                self.rank_15_1 = 0
                                self.count_15_2 = 0
                                self.rank_15_2 = 0
                                self.count_15_3 = 0
                                self.rank_15_3 = 0
                                self.count_15_4 = 0
                                self.rank_15_4 = 0
                                self.count_15_5 = 0
                                self.rank_15_5 = 0
                            if self.cand_has_15 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_15_1 == 0:
                                        self.rank_15_1 = self.next_rank_15
                                        self.next_rank_15 = self.next_rank_15 + 1
                                    self.count_15_1 = self.count_15_1 + 1
                                if prior_value == 2:
                                    if self.count_15_2 == 0:
                                        self.rank_15_2 = self.next_rank_15
                                        self.next_rank_15 = self.next_rank_15 + 1
                                    self.count_15_2 = self.count_15_2 + 1
                                if prior_value == 3:
                                    if self.count_15_3 == 0:
                                        self.rank_15_3 = self.next_rank_15
                                        self.next_rank_15 = self.next_rank_15 + 1
                                    self.count_15_3 = self.count_15_3 + 1
                                if prior_value == 4:
                                    if self.count_15_4 == 0:
                                        self.rank_15_4 = self.next_rank_15
                                        self.next_rank_15 = self.next_rank_15 + 1
                                    self.count_15_4 = self.count_15_4 + 1
                                if prior_value == 5:
                                    if self.count_15_5 == 0:
                                        self.rank_15_5 = self.next_rank_15
                                        self.next_rank_15 = self.next_rank_15 + 1
                                    self.count_15_5 = self.count_15_5 + 1
                        if self.status == 0:
                            self.prom_has_15 = 1
                            if sender == 0:
                                self.prom_15_0 = 1
                            if sender == 1:
                                self.prom_15_1 = 1
                            if sender == 2:
                                self.prom_15_2 = 1
                            if self.prom_15_0 + self.prom_15_1 + self.prom_15_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_15 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_15_1 > best_count or (self.count_15_1 == best_count and self.count_15_1 != 0 and self.rank_15_1 < best_rank):
                                            best_count = self.count_15_1
                                            best_rank = self.rank_15_1
                                            choice = self.num - self.num + 1
                                        if self.count_15_2 > best_count or (self.count_15_2 == best_count and self.count_15_2 != 0 and self.rank_15_2 < best_rank):
                                            best_count = self.count_15_2
                                            best_rank = self.rank_15_2
                                            choice = self.num - self.num + 2
                                        if self.count_15_3 > best_count or (self.count_15_3 == best_count and self.count_15_3 != 0 and self.rank_15_3 < best_rank):
                                            best_count = self.count_15_3
                                            best_rank = self.rank_15_3
                                            choice = self.num - self.num + 3
                                        if self.count_15_4 > best_count or (self.count_15_4 == best_count and self.count_15_4 != 0 and self.rank_15_4 < best_rank):
                                            best_count = self.count_15_4
                                            best_rank = self.rank_15_4
                                            choice = self.num - self.num + 4
                                        if self.count_15_5 > best_count or (self.count_15_5 == best_count and self.count_15_5 != 0 and self.rank_15_5 < best_rank):
                                            best_count = self.count_15_5
                                            best_rank = self.rank_15_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_15 = 1
                                    self.pv_15 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 16:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_16 = 1
                                self.next_rank_16 = 0
                                self.count_16_1 = 0
                                self.rank_16_1 = 0
                                self.count_16_2 = 0
                                self.rank_16_2 = 0
                                self.count_16_3 = 0
                                self.rank_16_3 = 0
                                self.count_16_4 = 0
                                self.rank_16_4 = 0
                                self.count_16_5 = 0
                                self.rank_16_5 = 0
                            if self.cand_has_16 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_16_1 == 0:
                                        self.rank_16_1 = self.next_rank_16
                                        self.next_rank_16 = self.next_rank_16 + 1
                                    self.count_16_1 = self.count_16_1 + 1
                                if prior_value == 2:
                                    if self.count_16_2 == 0:
                                        self.rank_16_2 = self.next_rank_16
                                        self.next_rank_16 = self.next_rank_16 + 1
                                    self.count_16_2 = self.count_16_2 + 1
                                if prior_value == 3:
                                    if self.count_16_3 == 0:
                                        self.rank_16_3 = self.next_rank_16
                                        self.next_rank_16 = self.next_rank_16 + 1
                                    self.count_16_3 = self.count_16_3 + 1
                                if prior_value == 4:
                                    if self.count_16_4 == 0:
                                        self.rank_16_4 = self.next_rank_16
                                        self.next_rank_16 = self.next_rank_16 + 1
                                    self.count_16_4 = self.count_16_4 + 1
                                if prior_value == 5:
                                    if self.count_16_5 == 0:
                                        self.rank_16_5 = self.next_rank_16
                                        self.next_rank_16 = self.next_rank_16 + 1
                                    self.count_16_5 = self.count_16_5 + 1
                        if self.status == 0:
                            self.prom_has_16 = 1
                            if sender == 0:
                                self.prom_16_0 = 1
                            if sender == 1:
                                self.prom_16_1 = 1
                            if sender == 2:
                                self.prom_16_2 = 1
                            if self.prom_16_0 + self.prom_16_1 + self.prom_16_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_16 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_16_1 > best_count or (self.count_16_1 == best_count and self.count_16_1 != 0 and self.rank_16_1 < best_rank):
                                            best_count = self.count_16_1
                                            best_rank = self.rank_16_1
                                            choice = self.num - self.num + 1
                                        if self.count_16_2 > best_count or (self.count_16_2 == best_count and self.count_16_2 != 0 and self.rank_16_2 < best_rank):
                                            best_count = self.count_16_2
                                            best_rank = self.rank_16_2
                                            choice = self.num - self.num + 2
                                        if self.count_16_3 > best_count or (self.count_16_3 == best_count and self.count_16_3 != 0 and self.rank_16_3 < best_rank):
                                            best_count = self.count_16_3
                                            best_rank = self.rank_16_3
                                            choice = self.num - self.num + 3
                                        if self.count_16_4 > best_count or (self.count_16_4 == best_count and self.count_16_4 != 0 and self.rank_16_4 < best_rank):
                                            best_count = self.count_16_4
                                            best_rank = self.rank_16_4
                                            choice = self.num - self.num + 4
                                        if self.count_16_5 > best_count or (self.count_16_5 == best_count and self.count_16_5 != 0 and self.rank_16_5 < best_rank):
                                            best_count = self.count_16_5
                                            best_rank = self.rank_16_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_16 = 1
                                    self.pv_16 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 17:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_17 = 1
                                self.next_rank_17 = 0
                                self.count_17_1 = 0
                                self.rank_17_1 = 0
                                self.count_17_2 = 0
                                self.rank_17_2 = 0
                                self.count_17_3 = 0
                                self.rank_17_3 = 0
                                self.count_17_4 = 0
                                self.rank_17_4 = 0
                                self.count_17_5 = 0
                                self.rank_17_5 = 0
                            if self.cand_has_17 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_17_1 == 0:
                                        self.rank_17_1 = self.next_rank_17
                                        self.next_rank_17 = self.next_rank_17 + 1
                                    self.count_17_1 = self.count_17_1 + 1
                                if prior_value == 2:
                                    if self.count_17_2 == 0:
                                        self.rank_17_2 = self.next_rank_17
                                        self.next_rank_17 = self.next_rank_17 + 1
                                    self.count_17_2 = self.count_17_2 + 1
                                if prior_value == 3:
                                    if self.count_17_3 == 0:
                                        self.rank_17_3 = self.next_rank_17
                                        self.next_rank_17 = self.next_rank_17 + 1
                                    self.count_17_3 = self.count_17_3 + 1
                                if prior_value == 4:
                                    if self.count_17_4 == 0:
                                        self.rank_17_4 = self.next_rank_17
                                        self.next_rank_17 = self.next_rank_17 + 1
                                    self.count_17_4 = self.count_17_4 + 1
                                if prior_value == 5:
                                    if self.count_17_5 == 0:
                                        self.rank_17_5 = self.next_rank_17
                                        self.next_rank_17 = self.next_rank_17 + 1
                                    self.count_17_5 = self.count_17_5 + 1
                        if self.status == 0:
                            self.prom_has_17 = 1
                            if sender == 0:
                                self.prom_17_0 = 1
                            if sender == 1:
                                self.prom_17_1 = 1
                            if sender == 2:
                                self.prom_17_2 = 1
                            if self.prom_17_0 + self.prom_17_1 + self.prom_17_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_17 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_17_1 > best_count or (self.count_17_1 == best_count and self.count_17_1 != 0 and self.rank_17_1 < best_rank):
                                            best_count = self.count_17_1
                                            best_rank = self.rank_17_1
                                            choice = self.num - self.num + 1
                                        if self.count_17_2 > best_count or (self.count_17_2 == best_count and self.count_17_2 != 0 and self.rank_17_2 < best_rank):
                                            best_count = self.count_17_2
                                            best_rank = self.rank_17_2
                                            choice = self.num - self.num + 2
                                        if self.count_17_3 > best_count or (self.count_17_3 == best_count and self.count_17_3 != 0 and self.rank_17_3 < best_rank):
                                            best_count = self.count_17_3
                                            best_rank = self.rank_17_3
                                            choice = self.num - self.num + 3
                                        if self.count_17_4 > best_count or (self.count_17_4 == best_count and self.count_17_4 != 0 and self.rank_17_4 < best_rank):
                                            best_count = self.count_17_4
                                            best_rank = self.rank_17_4
                                            choice = self.num - self.num + 4
                                        if self.count_17_5 > best_count or (self.count_17_5 == best_count and self.count_17_5 != 0 and self.rank_17_5 < best_rank):
                                            best_count = self.count_17_5
                                            best_rank = self.rank_17_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_17 = 1
                                    self.pv_17 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 18:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_18 = 1
                                self.next_rank_18 = 0
                                self.count_18_1 = 0
                                self.rank_18_1 = 0
                                self.count_18_2 = 0
                                self.rank_18_2 = 0
                                self.count_18_3 = 0
                                self.rank_18_3 = 0
                                self.count_18_4 = 0
                                self.rank_18_4 = 0
                                self.count_18_5 = 0
                                self.rank_18_5 = 0
                            if self.cand_has_18 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_18_1 == 0:
                                        self.rank_18_1 = self.next_rank_18
                                        self.next_rank_18 = self.next_rank_18 + 1
                                    self.count_18_1 = self.count_18_1 + 1
                                if prior_value == 2:
                                    if self.count_18_2 == 0:
                                        self.rank_18_2 = self.next_rank_18
                                        self.next_rank_18 = self.next_rank_18 + 1
                                    self.count_18_2 = self.count_18_2 + 1
                                if prior_value == 3:
                                    if self.count_18_3 == 0:
                                        self.rank_18_3 = self.next_rank_18
                                        self.next_rank_18 = self.next_rank_18 + 1
                                    self.count_18_3 = self.count_18_3 + 1
                                if prior_value == 4:
                                    if self.count_18_4 == 0:
                                        self.rank_18_4 = self.next_rank_18
                                        self.next_rank_18 = self.next_rank_18 + 1
                                    self.count_18_4 = self.count_18_4 + 1
                                if prior_value == 5:
                                    if self.count_18_5 == 0:
                                        self.rank_18_5 = self.next_rank_18
                                        self.next_rank_18 = self.next_rank_18 + 1
                                    self.count_18_5 = self.count_18_5 + 1
                        if self.status == 0:
                            self.prom_has_18 = 1
                            if sender == 0:
                                self.prom_18_0 = 1
                            if sender == 1:
                                self.prom_18_1 = 1
                            if sender == 2:
                                self.prom_18_2 = 1
                            if self.prom_18_0 + self.prom_18_1 + self.prom_18_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_18 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_18_1 > best_count or (self.count_18_1 == best_count and self.count_18_1 != 0 and self.rank_18_1 < best_rank):
                                            best_count = self.count_18_1
                                            best_rank = self.rank_18_1
                                            choice = self.num - self.num + 1
                                        if self.count_18_2 > best_count or (self.count_18_2 == best_count and self.count_18_2 != 0 and self.rank_18_2 < best_rank):
                                            best_count = self.count_18_2
                                            best_rank = self.rank_18_2
                                            choice = self.num - self.num + 2
                                        if self.count_18_3 > best_count or (self.count_18_3 == best_count and self.count_18_3 != 0 and self.rank_18_3 < best_rank):
                                            best_count = self.count_18_3
                                            best_rank = self.rank_18_3
                                            choice = self.num - self.num + 3
                                        if self.count_18_4 > best_count or (self.count_18_4 == best_count and self.count_18_4 != 0 and self.rank_18_4 < best_rank):
                                            best_count = self.count_18_4
                                            best_rank = self.rank_18_4
                                            choice = self.num - self.num + 4
                                        if self.count_18_5 > best_count or (self.count_18_5 == best_count and self.count_18_5 != 0 and self.rank_18_5 < best_rank):
                                            best_count = self.count_18_5
                                            best_rank = self.rank_18_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_18 = 1
                                    self.pv_18 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 19:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_19 = 1
                                self.next_rank_19 = 0
                                self.count_19_1 = 0
                                self.rank_19_1 = 0
                                self.count_19_2 = 0
                                self.rank_19_2 = 0
                                self.count_19_3 = 0
                                self.rank_19_3 = 0
                                self.count_19_4 = 0
                                self.rank_19_4 = 0
                                self.count_19_5 = 0
                                self.rank_19_5 = 0
                            if self.cand_has_19 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_19_1 == 0:
                                        self.rank_19_1 = self.next_rank_19
                                        self.next_rank_19 = self.next_rank_19 + 1
                                    self.count_19_1 = self.count_19_1 + 1
                                if prior_value == 2:
                                    if self.count_19_2 == 0:
                                        self.rank_19_2 = self.next_rank_19
                                        self.next_rank_19 = self.next_rank_19 + 1
                                    self.count_19_2 = self.count_19_2 + 1
                                if prior_value == 3:
                                    if self.count_19_3 == 0:
                                        self.rank_19_3 = self.next_rank_19
                                        self.next_rank_19 = self.next_rank_19 + 1
                                    self.count_19_3 = self.count_19_3 + 1
                                if prior_value == 4:
                                    if self.count_19_4 == 0:
                                        self.rank_19_4 = self.next_rank_19
                                        self.next_rank_19 = self.next_rank_19 + 1
                                    self.count_19_4 = self.count_19_4 + 1
                                if prior_value == 5:
                                    if self.count_19_5 == 0:
                                        self.rank_19_5 = self.next_rank_19
                                        self.next_rank_19 = self.next_rank_19 + 1
                                    self.count_19_5 = self.count_19_5 + 1
                        if self.status == 0:
                            self.prom_has_19 = 1
                            if sender == 0:
                                self.prom_19_0 = 1
                            if sender == 1:
                                self.prom_19_1 = 1
                            if sender == 2:
                                self.prom_19_2 = 1
                            if self.prom_19_0 + self.prom_19_1 + self.prom_19_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_19 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_19_1 > best_count or (self.count_19_1 == best_count and self.count_19_1 != 0 and self.rank_19_1 < best_rank):
                                            best_count = self.count_19_1
                                            best_rank = self.rank_19_1
                                            choice = self.num - self.num + 1
                                        if self.count_19_2 > best_count or (self.count_19_2 == best_count and self.count_19_2 != 0 and self.rank_19_2 < best_rank):
                                            best_count = self.count_19_2
                                            best_rank = self.rank_19_2
                                            choice = self.num - self.num + 2
                                        if self.count_19_3 > best_count or (self.count_19_3 == best_count and self.count_19_3 != 0 and self.rank_19_3 < best_rank):
                                            best_count = self.count_19_3
                                            best_rank = self.rank_19_3
                                            choice = self.num - self.num + 3
                                        if self.count_19_4 > best_count or (self.count_19_4 == best_count and self.count_19_4 != 0 and self.rank_19_4 < best_rank):
                                            best_count = self.count_19_4
                                            best_rank = self.rank_19_4
                                            choice = self.num - self.num + 4
                                        if self.count_19_5 > best_count or (self.count_19_5 == best_count and self.count_19_5 != 0 and self.rank_19_5 < best_rank):
                                            best_count = self.count_19_5
                                            best_rank = self.rank_19_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_19 = 1
                                    self.pv_19 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 20:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_20 = 1
                                self.next_rank_20 = 0
                                self.count_20_1 = 0
                                self.rank_20_1 = 0
                                self.count_20_2 = 0
                                self.rank_20_2 = 0
                                self.count_20_3 = 0
                                self.rank_20_3 = 0
                                self.count_20_4 = 0
                                self.rank_20_4 = 0
                                self.count_20_5 = 0
                                self.rank_20_5 = 0
                            if self.cand_has_20 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_20_1 == 0:
                                        self.rank_20_1 = self.next_rank_20
                                        self.next_rank_20 = self.next_rank_20 + 1
                                    self.count_20_1 = self.count_20_1 + 1
                                if prior_value == 2:
                                    if self.count_20_2 == 0:
                                        self.rank_20_2 = self.next_rank_20
                                        self.next_rank_20 = self.next_rank_20 + 1
                                    self.count_20_2 = self.count_20_2 + 1
                                if prior_value == 3:
                                    if self.count_20_3 == 0:
                                        self.rank_20_3 = self.next_rank_20
                                        self.next_rank_20 = self.next_rank_20 + 1
                                    self.count_20_3 = self.count_20_3 + 1
                                if prior_value == 4:
                                    if self.count_20_4 == 0:
                                        self.rank_20_4 = self.next_rank_20
                                        self.next_rank_20 = self.next_rank_20 + 1
                                    self.count_20_4 = self.count_20_4 + 1
                                if prior_value == 5:
                                    if self.count_20_5 == 0:
                                        self.rank_20_5 = self.next_rank_20
                                        self.next_rank_20 = self.next_rank_20 + 1
                                    self.count_20_5 = self.count_20_5 + 1
                        if self.status == 0:
                            self.prom_has_20 = 1
                            if sender == 0:
                                self.prom_20_0 = 1
                            if sender == 1:
                                self.prom_20_1 = 1
                            if sender == 2:
                                self.prom_20_2 = 1
                            if self.prom_20_0 + self.prom_20_1 + self.prom_20_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_20 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_20_1 > best_count or (self.count_20_1 == best_count and self.count_20_1 != 0 and self.rank_20_1 < best_rank):
                                            best_count = self.count_20_1
                                            best_rank = self.rank_20_1
                                            choice = self.num - self.num + 1
                                        if self.count_20_2 > best_count or (self.count_20_2 == best_count and self.count_20_2 != 0 and self.rank_20_2 < best_rank):
                                            best_count = self.count_20_2
                                            best_rank = self.rank_20_2
                                            choice = self.num - self.num + 2
                                        if self.count_20_3 > best_count or (self.count_20_3 == best_count and self.count_20_3 != 0 and self.rank_20_3 < best_rank):
                                            best_count = self.count_20_3
                                            best_rank = self.rank_20_3
                                            choice = self.num - self.num + 3
                                        if self.count_20_4 > best_count or (self.count_20_4 == best_count and self.count_20_4 != 0 and self.rank_20_4 < best_rank):
                                            best_count = self.count_20_4
                                            best_rank = self.rank_20_4
                                            choice = self.num - self.num + 4
                                        if self.count_20_5 > best_count or (self.count_20_5 == best_count and self.count_20_5 != 0 and self.rank_20_5 < best_rank):
                                            best_count = self.count_20_5
                                            best_rank = self.rank_20_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_20 = 1
                                    self.pv_20 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 21:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_21 = 1
                                self.next_rank_21 = 0
                                self.count_21_1 = 0
                                self.rank_21_1 = 0
                                self.count_21_2 = 0
                                self.rank_21_2 = 0
                                self.count_21_3 = 0
                                self.rank_21_3 = 0
                                self.count_21_4 = 0
                                self.rank_21_4 = 0
                                self.count_21_5 = 0
                                self.rank_21_5 = 0
                            if self.cand_has_21 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_21_1 == 0:
                                        self.rank_21_1 = self.next_rank_21
                                        self.next_rank_21 = self.next_rank_21 + 1
                                    self.count_21_1 = self.count_21_1 + 1
                                if prior_value == 2:
                                    if self.count_21_2 == 0:
                                        self.rank_21_2 = self.next_rank_21
                                        self.next_rank_21 = self.next_rank_21 + 1
                                    self.count_21_2 = self.count_21_2 + 1
                                if prior_value == 3:
                                    if self.count_21_3 == 0:
                                        self.rank_21_3 = self.next_rank_21
                                        self.next_rank_21 = self.next_rank_21 + 1
                                    self.count_21_3 = self.count_21_3 + 1
                                if prior_value == 4:
                                    if self.count_21_4 == 0:
                                        self.rank_21_4 = self.next_rank_21
                                        self.next_rank_21 = self.next_rank_21 + 1
                                    self.count_21_4 = self.count_21_4 + 1
                                if prior_value == 5:
                                    if self.count_21_5 == 0:
                                        self.rank_21_5 = self.next_rank_21
                                        self.next_rank_21 = self.next_rank_21 + 1
                                    self.count_21_5 = self.count_21_5 + 1
                        if self.status == 0:
                            self.prom_has_21 = 1
                            if sender == 0:
                                self.prom_21_0 = 1
                            if sender == 1:
                                self.prom_21_1 = 1
                            if sender == 2:
                                self.prom_21_2 = 1
                            if self.prom_21_0 + self.prom_21_1 + self.prom_21_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_21 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_21_1 > best_count or (self.count_21_1 == best_count and self.count_21_1 != 0 and self.rank_21_1 < best_rank):
                                            best_count = self.count_21_1
                                            best_rank = self.rank_21_1
                                            choice = self.num - self.num + 1
                                        if self.count_21_2 > best_count or (self.count_21_2 == best_count and self.count_21_2 != 0 and self.rank_21_2 < best_rank):
                                            best_count = self.count_21_2
                                            best_rank = self.rank_21_2
                                            choice = self.num - self.num + 2
                                        if self.count_21_3 > best_count or (self.count_21_3 == best_count and self.count_21_3 != 0 and self.rank_21_3 < best_rank):
                                            best_count = self.count_21_3
                                            best_rank = self.rank_21_3
                                            choice = self.num - self.num + 3
                                        if self.count_21_4 > best_count or (self.count_21_4 == best_count and self.count_21_4 != 0 and self.rank_21_4 < best_rank):
                                            best_count = self.count_21_4
                                            best_rank = self.rank_21_4
                                            choice = self.num - self.num + 4
                                        if self.count_21_5 > best_count or (self.count_21_5 == best_count and self.count_21_5 != 0 and self.rank_21_5 < best_rank):
                                            best_count = self.count_21_5
                                            best_rank = self.rank_21_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_21 = 1
                                    self.pv_21 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 22:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_22 = 1
                                self.next_rank_22 = 0
                                self.count_22_1 = 0
                                self.rank_22_1 = 0
                                self.count_22_2 = 0
                                self.rank_22_2 = 0
                                self.count_22_3 = 0
                                self.rank_22_3 = 0
                                self.count_22_4 = 0
                                self.rank_22_4 = 0
                                self.count_22_5 = 0
                                self.rank_22_5 = 0
                            if self.cand_has_22 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_22_1 == 0:
                                        self.rank_22_1 = self.next_rank_22
                                        self.next_rank_22 = self.next_rank_22 + 1
                                    self.count_22_1 = self.count_22_1 + 1
                                if prior_value == 2:
                                    if self.count_22_2 == 0:
                                        self.rank_22_2 = self.next_rank_22
                                        self.next_rank_22 = self.next_rank_22 + 1
                                    self.count_22_2 = self.count_22_2 + 1
                                if prior_value == 3:
                                    if self.count_22_3 == 0:
                                        self.rank_22_3 = self.next_rank_22
                                        self.next_rank_22 = self.next_rank_22 + 1
                                    self.count_22_3 = self.count_22_3 + 1
                                if prior_value == 4:
                                    if self.count_22_4 == 0:
                                        self.rank_22_4 = self.next_rank_22
                                        self.next_rank_22 = self.next_rank_22 + 1
                                    self.count_22_4 = self.count_22_4 + 1
                                if prior_value == 5:
                                    if self.count_22_5 == 0:
                                        self.rank_22_5 = self.next_rank_22
                                        self.next_rank_22 = self.next_rank_22 + 1
                                    self.count_22_5 = self.count_22_5 + 1
                        if self.status == 0:
                            self.prom_has_22 = 1
                            if sender == 0:
                                self.prom_22_0 = 1
                            if sender == 1:
                                self.prom_22_1 = 1
                            if sender == 2:
                                self.prom_22_2 = 1
                            if self.prom_22_0 + self.prom_22_1 + self.prom_22_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_22 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_22_1 > best_count or (self.count_22_1 == best_count and self.count_22_1 != 0 and self.rank_22_1 < best_rank):
                                            best_count = self.count_22_1
                                            best_rank = self.rank_22_1
                                            choice = self.num - self.num + 1
                                        if self.count_22_2 > best_count or (self.count_22_2 == best_count and self.count_22_2 != 0 and self.rank_22_2 < best_rank):
                                            best_count = self.count_22_2
                                            best_rank = self.rank_22_2
                                            choice = self.num - self.num + 2
                                        if self.count_22_3 > best_count or (self.count_22_3 == best_count and self.count_22_3 != 0 and self.rank_22_3 < best_rank):
                                            best_count = self.count_22_3
                                            best_rank = self.rank_22_3
                                            choice = self.num - self.num + 3
                                        if self.count_22_4 > best_count or (self.count_22_4 == best_count and self.count_22_4 != 0 and self.rank_22_4 < best_rank):
                                            best_count = self.count_22_4
                                            best_rank = self.rank_22_4
                                            choice = self.num - self.num + 4
                                        if self.count_22_5 > best_count or (self.count_22_5 == best_count and self.count_22_5 != 0 and self.rank_22_5 < best_rank):
                                            best_count = self.count_22_5
                                            best_rank = self.rank_22_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_22 = 1
                                    self.pv_22 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 23:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_23 = 1
                                self.next_rank_23 = 0
                                self.count_23_1 = 0
                                self.rank_23_1 = 0
                                self.count_23_2 = 0
                                self.rank_23_2 = 0
                                self.count_23_3 = 0
                                self.rank_23_3 = 0
                                self.count_23_4 = 0
                                self.rank_23_4 = 0
                                self.count_23_5 = 0
                                self.rank_23_5 = 0
                            if self.cand_has_23 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_23_1 == 0:
                                        self.rank_23_1 = self.next_rank_23
                                        self.next_rank_23 = self.next_rank_23 + 1
                                    self.count_23_1 = self.count_23_1 + 1
                                if prior_value == 2:
                                    if self.count_23_2 == 0:
                                        self.rank_23_2 = self.next_rank_23
                                        self.next_rank_23 = self.next_rank_23 + 1
                                    self.count_23_2 = self.count_23_2 + 1
                                if prior_value == 3:
                                    if self.count_23_3 == 0:
                                        self.rank_23_3 = self.next_rank_23
                                        self.next_rank_23 = self.next_rank_23 + 1
                                    self.count_23_3 = self.count_23_3 + 1
                                if prior_value == 4:
                                    if self.count_23_4 == 0:
                                        self.rank_23_4 = self.next_rank_23
                                        self.next_rank_23 = self.next_rank_23 + 1
                                    self.count_23_4 = self.count_23_4 + 1
                                if prior_value == 5:
                                    if self.count_23_5 == 0:
                                        self.rank_23_5 = self.next_rank_23
                                        self.next_rank_23 = self.next_rank_23 + 1
                                    self.count_23_5 = self.count_23_5 + 1
                        if self.status == 0:
                            self.prom_has_23 = 1
                            if sender == 0:
                                self.prom_23_0 = 1
                            if sender == 1:
                                self.prom_23_1 = 1
                            if sender == 2:
                                self.prom_23_2 = 1
                            if self.prom_23_0 + self.prom_23_1 + self.prom_23_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_23 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_23_1 > best_count or (self.count_23_1 == best_count and self.count_23_1 != 0 and self.rank_23_1 < best_rank):
                                            best_count = self.count_23_1
                                            best_rank = self.rank_23_1
                                            choice = self.num - self.num + 1
                                        if self.count_23_2 > best_count or (self.count_23_2 == best_count and self.count_23_2 != 0 and self.rank_23_2 < best_rank):
                                            best_count = self.count_23_2
                                            best_rank = self.rank_23_2
                                            choice = self.num - self.num + 2
                                        if self.count_23_3 > best_count or (self.count_23_3 == best_count and self.count_23_3 != 0 and self.rank_23_3 < best_rank):
                                            best_count = self.count_23_3
                                            best_rank = self.rank_23_3
                                            choice = self.num - self.num + 3
                                        if self.count_23_4 > best_count or (self.count_23_4 == best_count and self.count_23_4 != 0 and self.rank_23_4 < best_rank):
                                            best_count = self.count_23_4
                                            best_rank = self.rank_23_4
                                            choice = self.num - self.num + 4
                                        if self.count_23_5 > best_count or (self.count_23_5 == best_count and self.count_23_5 != 0 and self.rank_23_5 < best_rank):
                                            best_count = self.count_23_5
                                            best_rank = self.rank_23_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_23 = 1
                                    self.pv_23 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 24:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_24 = 1
                                self.next_rank_24 = 0
                                self.count_24_1 = 0
                                self.rank_24_1 = 0
                                self.count_24_2 = 0
                                self.rank_24_2 = 0
                                self.count_24_3 = 0
                                self.rank_24_3 = 0
                                self.count_24_4 = 0
                                self.rank_24_4 = 0
                                self.count_24_5 = 0
                                self.rank_24_5 = 0
                            if self.cand_has_24 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_24_1 == 0:
                                        self.rank_24_1 = self.next_rank_24
                                        self.next_rank_24 = self.next_rank_24 + 1
                                    self.count_24_1 = self.count_24_1 + 1
                                if prior_value == 2:
                                    if self.count_24_2 == 0:
                                        self.rank_24_2 = self.next_rank_24
                                        self.next_rank_24 = self.next_rank_24 + 1
                                    self.count_24_2 = self.count_24_2 + 1
                                if prior_value == 3:
                                    if self.count_24_3 == 0:
                                        self.rank_24_3 = self.next_rank_24
                                        self.next_rank_24 = self.next_rank_24 + 1
                                    self.count_24_3 = self.count_24_3 + 1
                                if prior_value == 4:
                                    if self.count_24_4 == 0:
                                        self.rank_24_4 = self.next_rank_24
                                        self.next_rank_24 = self.next_rank_24 + 1
                                    self.count_24_4 = self.count_24_4 + 1
                                if prior_value == 5:
                                    if self.count_24_5 == 0:
                                        self.rank_24_5 = self.next_rank_24
                                        self.next_rank_24 = self.next_rank_24 + 1
                                    self.count_24_5 = self.count_24_5 + 1
                        if self.status == 0:
                            self.prom_has_24 = 1
                            if sender == 0:
                                self.prom_24_0 = 1
                            if sender == 1:
                                self.prom_24_1 = 1
                            if sender == 2:
                                self.prom_24_2 = 1
                            if self.prom_24_0 + self.prom_24_1 + self.prom_24_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_24 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_24_1 > best_count or (self.count_24_1 == best_count and self.count_24_1 != 0 and self.rank_24_1 < best_rank):
                                            best_count = self.count_24_1
                                            best_rank = self.rank_24_1
                                            choice = self.num - self.num + 1
                                        if self.count_24_2 > best_count or (self.count_24_2 == best_count and self.count_24_2 != 0 and self.rank_24_2 < best_rank):
                                            best_count = self.count_24_2
                                            best_rank = self.rank_24_2
                                            choice = self.num - self.num + 2
                                        if self.count_24_3 > best_count or (self.count_24_3 == best_count and self.count_24_3 != 0 and self.rank_24_3 < best_rank):
                                            best_count = self.count_24_3
                                            best_rank = self.rank_24_3
                                            choice = self.num - self.num + 3
                                        if self.count_24_4 > best_count or (self.count_24_4 == best_count and self.count_24_4 != 0 and self.rank_24_4 < best_rank):
                                            best_count = self.count_24_4
                                            best_rank = self.rank_24_4
                                            choice = self.num - self.num + 4
                                        if self.count_24_5 > best_count or (self.count_24_5 == best_count and self.count_24_5 != 0 and self.rank_24_5 < best_rank):
                                            best_count = self.count_24_5
                                            best_rank = self.rank_24_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_24 = 1
                                    self.pv_24 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 25:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_25 = 1
                                self.next_rank_25 = 0
                                self.count_25_1 = 0
                                self.rank_25_1 = 0
                                self.count_25_2 = 0
                                self.rank_25_2 = 0
                                self.count_25_3 = 0
                                self.rank_25_3 = 0
                                self.count_25_4 = 0
                                self.rank_25_4 = 0
                                self.count_25_5 = 0
                                self.rank_25_5 = 0
                            if self.cand_has_25 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_25_1 == 0:
                                        self.rank_25_1 = self.next_rank_25
                                        self.next_rank_25 = self.next_rank_25 + 1
                                    self.count_25_1 = self.count_25_1 + 1
                                if prior_value == 2:
                                    if self.count_25_2 == 0:
                                        self.rank_25_2 = self.next_rank_25
                                        self.next_rank_25 = self.next_rank_25 + 1
                                    self.count_25_2 = self.count_25_2 + 1
                                if prior_value == 3:
                                    if self.count_25_3 == 0:
                                        self.rank_25_3 = self.next_rank_25
                                        self.next_rank_25 = self.next_rank_25 + 1
                                    self.count_25_3 = self.count_25_3 + 1
                                if prior_value == 4:
                                    if self.count_25_4 == 0:
                                        self.rank_25_4 = self.next_rank_25
                                        self.next_rank_25 = self.next_rank_25 + 1
                                    self.count_25_4 = self.count_25_4 + 1
                                if prior_value == 5:
                                    if self.count_25_5 == 0:
                                        self.rank_25_5 = self.next_rank_25
                                        self.next_rank_25 = self.next_rank_25 + 1
                                    self.count_25_5 = self.count_25_5 + 1
                        if self.status == 0:
                            self.prom_has_25 = 1
                            if sender == 0:
                                self.prom_25_0 = 1
                            if sender == 1:
                                self.prom_25_1 = 1
                            if sender == 2:
                                self.prom_25_2 = 1
                            if self.prom_25_0 + self.prom_25_1 + self.prom_25_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_25 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_25_1 > best_count or (self.count_25_1 == best_count and self.count_25_1 != 0 and self.rank_25_1 < best_rank):
                                            best_count = self.count_25_1
                                            best_rank = self.rank_25_1
                                            choice = self.num - self.num + 1
                                        if self.count_25_2 > best_count or (self.count_25_2 == best_count and self.count_25_2 != 0 and self.rank_25_2 < best_rank):
                                            best_count = self.count_25_2
                                            best_rank = self.rank_25_2
                                            choice = self.num - self.num + 2
                                        if self.count_25_3 > best_count or (self.count_25_3 == best_count and self.count_25_3 != 0 and self.rank_25_3 < best_rank):
                                            best_count = self.count_25_3
                                            best_rank = self.rank_25_3
                                            choice = self.num - self.num + 3
                                        if self.count_25_4 > best_count or (self.count_25_4 == best_count and self.count_25_4 != 0 and self.rank_25_4 < best_rank):
                                            best_count = self.count_25_4
                                            best_rank = self.rank_25_4
                                            choice = self.num - self.num + 4
                                        if self.count_25_5 > best_count or (self.count_25_5 == best_count and self.count_25_5 != 0 and self.rank_25_5 < best_rank):
                                            best_count = self.count_25_5
                                            best_rank = self.rank_25_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_25 = 1
                                    self.pv_25 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 26:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_26 = 1
                                self.next_rank_26 = 0
                                self.count_26_1 = 0
                                self.rank_26_1 = 0
                                self.count_26_2 = 0
                                self.rank_26_2 = 0
                                self.count_26_3 = 0
                                self.rank_26_3 = 0
                                self.count_26_4 = 0
                                self.rank_26_4 = 0
                                self.count_26_5 = 0
                                self.rank_26_5 = 0
                            if self.cand_has_26 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_26_1 == 0:
                                        self.rank_26_1 = self.next_rank_26
                                        self.next_rank_26 = self.next_rank_26 + 1
                                    self.count_26_1 = self.count_26_1 + 1
                                if prior_value == 2:
                                    if self.count_26_2 == 0:
                                        self.rank_26_2 = self.next_rank_26
                                        self.next_rank_26 = self.next_rank_26 + 1
                                    self.count_26_2 = self.count_26_2 + 1
                                if prior_value == 3:
                                    if self.count_26_3 == 0:
                                        self.rank_26_3 = self.next_rank_26
                                        self.next_rank_26 = self.next_rank_26 + 1
                                    self.count_26_3 = self.count_26_3 + 1
                                if prior_value == 4:
                                    if self.count_26_4 == 0:
                                        self.rank_26_4 = self.next_rank_26
                                        self.next_rank_26 = self.next_rank_26 + 1
                                    self.count_26_4 = self.count_26_4 + 1
                                if prior_value == 5:
                                    if self.count_26_5 == 0:
                                        self.rank_26_5 = self.next_rank_26
                                        self.next_rank_26 = self.next_rank_26 + 1
                                    self.count_26_5 = self.count_26_5 + 1
                        if self.status == 0:
                            self.prom_has_26 = 1
                            if sender == 0:
                                self.prom_26_0 = 1
                            if sender == 1:
                                self.prom_26_1 = 1
                            if sender == 2:
                                self.prom_26_2 = 1
                            if self.prom_26_0 + self.prom_26_1 + self.prom_26_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_26 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_26_1 > best_count or (self.count_26_1 == best_count and self.count_26_1 != 0 and self.rank_26_1 < best_rank):
                                            best_count = self.count_26_1
                                            best_rank = self.rank_26_1
                                            choice = self.num - self.num + 1
                                        if self.count_26_2 > best_count or (self.count_26_2 == best_count and self.count_26_2 != 0 and self.rank_26_2 < best_rank):
                                            best_count = self.count_26_2
                                            best_rank = self.rank_26_2
                                            choice = self.num - self.num + 2
                                        if self.count_26_3 > best_count or (self.count_26_3 == best_count and self.count_26_3 != 0 and self.rank_26_3 < best_rank):
                                            best_count = self.count_26_3
                                            best_rank = self.rank_26_3
                                            choice = self.num - self.num + 3
                                        if self.count_26_4 > best_count or (self.count_26_4 == best_count and self.count_26_4 != 0 and self.rank_26_4 < best_rank):
                                            best_count = self.count_26_4
                                            best_rank = self.rank_26_4
                                            choice = self.num - self.num + 4
                                        if self.count_26_5 > best_count or (self.count_26_5 == best_count and self.count_26_5 != 0 and self.rank_26_5 < best_rank):
                                            best_count = self.count_26_5
                                            best_rank = self.rank_26_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_26 = 1
                                    self.pv_26 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 27:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_27 = 1
                                self.next_rank_27 = 0
                                self.count_27_1 = 0
                                self.rank_27_1 = 0
                                self.count_27_2 = 0
                                self.rank_27_2 = 0
                                self.count_27_3 = 0
                                self.rank_27_3 = 0
                                self.count_27_4 = 0
                                self.rank_27_4 = 0
                                self.count_27_5 = 0
                                self.rank_27_5 = 0
                            if self.cand_has_27 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_27_1 == 0:
                                        self.rank_27_1 = self.next_rank_27
                                        self.next_rank_27 = self.next_rank_27 + 1
                                    self.count_27_1 = self.count_27_1 + 1
                                if prior_value == 2:
                                    if self.count_27_2 == 0:
                                        self.rank_27_2 = self.next_rank_27
                                        self.next_rank_27 = self.next_rank_27 + 1
                                    self.count_27_2 = self.count_27_2 + 1
                                if prior_value == 3:
                                    if self.count_27_3 == 0:
                                        self.rank_27_3 = self.next_rank_27
                                        self.next_rank_27 = self.next_rank_27 + 1
                                    self.count_27_3 = self.count_27_3 + 1
                                if prior_value == 4:
                                    if self.count_27_4 == 0:
                                        self.rank_27_4 = self.next_rank_27
                                        self.next_rank_27 = self.next_rank_27 + 1
                                    self.count_27_4 = self.count_27_4 + 1
                                if prior_value == 5:
                                    if self.count_27_5 == 0:
                                        self.rank_27_5 = self.next_rank_27
                                        self.next_rank_27 = self.next_rank_27 + 1
                                    self.count_27_5 = self.count_27_5 + 1
                        if self.status == 0:
                            self.prom_has_27 = 1
                            if sender == 0:
                                self.prom_27_0 = 1
                            if sender == 1:
                                self.prom_27_1 = 1
                            if sender == 2:
                                self.prom_27_2 = 1
                            if self.prom_27_0 + self.prom_27_1 + self.prom_27_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_27 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_27_1 > best_count or (self.count_27_1 == best_count and self.count_27_1 != 0 and self.rank_27_1 < best_rank):
                                            best_count = self.count_27_1
                                            best_rank = self.rank_27_1
                                            choice = self.num - self.num + 1
                                        if self.count_27_2 > best_count or (self.count_27_2 == best_count and self.count_27_2 != 0 and self.rank_27_2 < best_rank):
                                            best_count = self.count_27_2
                                            best_rank = self.rank_27_2
                                            choice = self.num - self.num + 2
                                        if self.count_27_3 > best_count or (self.count_27_3 == best_count and self.count_27_3 != 0 and self.rank_27_3 < best_rank):
                                            best_count = self.count_27_3
                                            best_rank = self.rank_27_3
                                            choice = self.num - self.num + 3
                                        if self.count_27_4 > best_count or (self.count_27_4 == best_count and self.count_27_4 != 0 and self.rank_27_4 < best_rank):
                                            best_count = self.count_27_4
                                            best_rank = self.rank_27_4
                                            choice = self.num - self.num + 4
                                        if self.count_27_5 > best_count or (self.count_27_5 == best_count and self.count_27_5 != 0 and self.rank_27_5 < best_rank):
                                            best_count = self.count_27_5
                                            best_rank = self.rank_27_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_27 = 1
                                    self.pv_27 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 28:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_28 = 1
                                self.next_rank_28 = 0
                                self.count_28_1 = 0
                                self.rank_28_1 = 0
                                self.count_28_2 = 0
                                self.rank_28_2 = 0
                                self.count_28_3 = 0
                                self.rank_28_3 = 0
                                self.count_28_4 = 0
                                self.rank_28_4 = 0
                                self.count_28_5 = 0
                                self.rank_28_5 = 0
                            if self.cand_has_28 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_28_1 == 0:
                                        self.rank_28_1 = self.next_rank_28
                                        self.next_rank_28 = self.next_rank_28 + 1
                                    self.count_28_1 = self.count_28_1 + 1
                                if prior_value == 2:
                                    if self.count_28_2 == 0:
                                        self.rank_28_2 = self.next_rank_28
                                        self.next_rank_28 = self.next_rank_28 + 1
                                    self.count_28_2 = self.count_28_2 + 1
                                if prior_value == 3:
                                    if self.count_28_3 == 0:
                                        self.rank_28_3 = self.next_rank_28
                                        self.next_rank_28 = self.next_rank_28 + 1
                                    self.count_28_3 = self.count_28_3 + 1
                                if prior_value == 4:
                                    if self.count_28_4 == 0:
                                        self.rank_28_4 = self.next_rank_28
                                        self.next_rank_28 = self.next_rank_28 + 1
                                    self.count_28_4 = self.count_28_4 + 1
                                if prior_value == 5:
                                    if self.count_28_5 == 0:
                                        self.rank_28_5 = self.next_rank_28
                                        self.next_rank_28 = self.next_rank_28 + 1
                                    self.count_28_5 = self.count_28_5 + 1
                        if self.status == 0:
                            self.prom_has_28 = 1
                            if sender == 0:
                                self.prom_28_0 = 1
                            if sender == 1:
                                self.prom_28_1 = 1
                            if sender == 2:
                                self.prom_28_2 = 1
                            if self.prom_28_0 + self.prom_28_1 + self.prom_28_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_28 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_28_1 > best_count or (self.count_28_1 == best_count and self.count_28_1 != 0 and self.rank_28_1 < best_rank):
                                            best_count = self.count_28_1
                                            best_rank = self.rank_28_1
                                            choice = self.num - self.num + 1
                                        if self.count_28_2 > best_count or (self.count_28_2 == best_count and self.count_28_2 != 0 and self.rank_28_2 < best_rank):
                                            best_count = self.count_28_2
                                            best_rank = self.rank_28_2
                                            choice = self.num - self.num + 2
                                        if self.count_28_3 > best_count or (self.count_28_3 == best_count and self.count_28_3 != 0 and self.rank_28_3 < best_rank):
                                            best_count = self.count_28_3
                                            best_rank = self.rank_28_3
                                            choice = self.num - self.num + 3
                                        if self.count_28_4 > best_count or (self.count_28_4 == best_count and self.count_28_4 != 0 and self.rank_28_4 < best_rank):
                                            best_count = self.count_28_4
                                            best_rank = self.rank_28_4
                                            choice = self.num - self.num + 4
                                        if self.count_28_5 > best_count or (self.count_28_5 == best_count and self.count_28_5 != 0 and self.rank_28_5 < best_rank):
                                            best_count = self.count_28_5
                                            best_rank = self.rank_28_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_28 = 1
                                    self.pv_28 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 29:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_29 = 1
                                self.next_rank_29 = 0
                                self.count_29_1 = 0
                                self.rank_29_1 = 0
                                self.count_29_2 = 0
                                self.rank_29_2 = 0
                                self.count_29_3 = 0
                                self.rank_29_3 = 0
                                self.count_29_4 = 0
                                self.rank_29_4 = 0
                                self.count_29_5 = 0
                                self.rank_29_5 = 0
                            if self.cand_has_29 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_29_1 == 0:
                                        self.rank_29_1 = self.next_rank_29
                                        self.next_rank_29 = self.next_rank_29 + 1
                                    self.count_29_1 = self.count_29_1 + 1
                                if prior_value == 2:
                                    if self.count_29_2 == 0:
                                        self.rank_29_2 = self.next_rank_29
                                        self.next_rank_29 = self.next_rank_29 + 1
                                    self.count_29_2 = self.count_29_2 + 1
                                if prior_value == 3:
                                    if self.count_29_3 == 0:
                                        self.rank_29_3 = self.next_rank_29
                                        self.next_rank_29 = self.next_rank_29 + 1
                                    self.count_29_3 = self.count_29_3 + 1
                                if prior_value == 4:
                                    if self.count_29_4 == 0:
                                        self.rank_29_4 = self.next_rank_29
                                        self.next_rank_29 = self.next_rank_29 + 1
                                    self.count_29_4 = self.count_29_4 + 1
                                if prior_value == 5:
                                    if self.count_29_5 == 0:
                                        self.rank_29_5 = self.next_rank_29
                                        self.next_rank_29 = self.next_rank_29 + 1
                                    self.count_29_5 = self.count_29_5 + 1
                        if self.status == 0:
                            self.prom_has_29 = 1
                            if sender == 0:
                                self.prom_29_0 = 1
                            if sender == 1:
                                self.prom_29_1 = 1
                            if sender == 2:
                                self.prom_29_2 = 1
                            if self.prom_29_0 + self.prom_29_1 + self.prom_29_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_29 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_29_1 > best_count or (self.count_29_1 == best_count and self.count_29_1 != 0 and self.rank_29_1 < best_rank):
                                            best_count = self.count_29_1
                                            best_rank = self.rank_29_1
                                            choice = self.num - self.num + 1
                                        if self.count_29_2 > best_count or (self.count_29_2 == best_count and self.count_29_2 != 0 and self.rank_29_2 < best_rank):
                                            best_count = self.count_29_2
                                            best_rank = self.rank_29_2
                                            choice = self.num - self.num + 2
                                        if self.count_29_3 > best_count or (self.count_29_3 == best_count and self.count_29_3 != 0 and self.rank_29_3 < best_rank):
                                            best_count = self.count_29_3
                                            best_rank = self.rank_29_3
                                            choice = self.num - self.num + 3
                                        if self.count_29_4 > best_count or (self.count_29_4 == best_count and self.count_29_4 != 0 and self.rank_29_4 < best_rank):
                                            best_count = self.count_29_4
                                            best_rank = self.rank_29_4
                                            choice = self.num - self.num + 4
                                        if self.count_29_5 > best_count or (self.count_29_5 == best_count and self.count_29_5 != 0 and self.rank_29_5 < best_rank):
                                            best_count = self.count_29_5
                                            best_rank = self.rank_29_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_29 = 1
                                    self.pv_29 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 30:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_30 = 1
                                self.next_rank_30 = 0
                                self.count_30_1 = 0
                                self.rank_30_1 = 0
                                self.count_30_2 = 0
                                self.rank_30_2 = 0
                                self.count_30_3 = 0
                                self.rank_30_3 = 0
                                self.count_30_4 = 0
                                self.rank_30_4 = 0
                                self.count_30_5 = 0
                                self.rank_30_5 = 0
                            if self.cand_has_30 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_30_1 == 0:
                                        self.rank_30_1 = self.next_rank_30
                                        self.next_rank_30 = self.next_rank_30 + 1
                                    self.count_30_1 = self.count_30_1 + 1
                                if prior_value == 2:
                                    if self.count_30_2 == 0:
                                        self.rank_30_2 = self.next_rank_30
                                        self.next_rank_30 = self.next_rank_30 + 1
                                    self.count_30_2 = self.count_30_2 + 1
                                if prior_value == 3:
                                    if self.count_30_3 == 0:
                                        self.rank_30_3 = self.next_rank_30
                                        self.next_rank_30 = self.next_rank_30 + 1
                                    self.count_30_3 = self.count_30_3 + 1
                                if prior_value == 4:
                                    if self.count_30_4 == 0:
                                        self.rank_30_4 = self.next_rank_30
                                        self.next_rank_30 = self.next_rank_30 + 1
                                    self.count_30_4 = self.count_30_4 + 1
                                if prior_value == 5:
                                    if self.count_30_5 == 0:
                                        self.rank_30_5 = self.next_rank_30
                                        self.next_rank_30 = self.next_rank_30 + 1
                                    self.count_30_5 = self.count_30_5 + 1
                        if self.status == 0:
                            self.prom_has_30 = 1
                            if sender == 0:
                                self.prom_30_0 = 1
                            if sender == 1:
                                self.prom_30_1 = 1
                            if sender == 2:
                                self.prom_30_2 = 1
                            if self.prom_30_0 + self.prom_30_1 + self.prom_30_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_30 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_30_1 > best_count or (self.count_30_1 == best_count and self.count_30_1 != 0 and self.rank_30_1 < best_rank):
                                            best_count = self.count_30_1
                                            best_rank = self.rank_30_1
                                            choice = self.num - self.num + 1
                                        if self.count_30_2 > best_count or (self.count_30_2 == best_count and self.count_30_2 != 0 and self.rank_30_2 < best_rank):
                                            best_count = self.count_30_2
                                            best_rank = self.rank_30_2
                                            choice = self.num - self.num + 2
                                        if self.count_30_3 > best_count or (self.count_30_3 == best_count and self.count_30_3 != 0 and self.rank_30_3 < best_rank):
                                            best_count = self.count_30_3
                                            best_rank = self.rank_30_3
                                            choice = self.num - self.num + 3
                                        if self.count_30_4 > best_count or (self.count_30_4 == best_count and self.count_30_4 != 0 and self.rank_30_4 < best_rank):
                                            best_count = self.count_30_4
                                            best_rank = self.rank_30_4
                                            choice = self.num - self.num + 4
                                        if self.count_30_5 > best_count or (self.count_30_5 == best_count and self.count_30_5 != 0 and self.rank_30_5 < best_rank):
                                            best_count = self.count_30_5
                                            best_rank = self.rank_30_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_30 = 1
                                    self.pv_30 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                    if number == 31:
                        if prior_value != 0:
                            if present == 0:
                                self.cand_has_31 = 1
                                self.next_rank_31 = 0
                                self.count_31_1 = 0
                                self.rank_31_1 = 0
                                self.count_31_2 = 0
                                self.rank_31_2 = 0
                                self.count_31_3 = 0
                                self.rank_31_3 = 0
                                self.count_31_4 = 0
                                self.rank_31_4 = 0
                                self.count_31_5 = 0
                                self.rank_31_5 = 0
                            if self.cand_has_31 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                if prior_value == 1:
                                    if self.count_31_1 == 0:
                                        self.rank_31_1 = self.next_rank_31
                                        self.next_rank_31 = self.next_rank_31 + 1
                                    self.count_31_1 = self.count_31_1 + 1
                                if prior_value == 2:
                                    if self.count_31_2 == 0:
                                        self.rank_31_2 = self.next_rank_31
                                        self.next_rank_31 = self.next_rank_31 + 1
                                    self.count_31_2 = self.count_31_2 + 1
                                if prior_value == 3:
                                    if self.count_31_3 == 0:
                                        self.rank_31_3 = self.next_rank_31
                                        self.next_rank_31 = self.next_rank_31 + 1
                                    self.count_31_3 = self.count_31_3 + 1
                                if prior_value == 4:
                                    if self.count_31_4 == 0:
                                        self.rank_31_4 = self.next_rank_31
                                        self.next_rank_31 = self.next_rank_31 + 1
                                    self.count_31_4 = self.count_31_4 + 1
                                if prior_value == 5:
                                    if self.count_31_5 == 0:
                                        self.rank_31_5 = self.next_rank_31
                                        self.next_rank_31 = self.next_rank_31 + 1
                                    self.count_31_5 = self.count_31_5 + 1
                        if self.status == 0:
                            self.prom_has_31 = 1
                            if sender == 0:
                                self.prom_31_0 = 1
                            if sender == 1:
                                self.prom_31_1 = 1
                            if sender == 2:
                                self.prom_31_2 = 1
                            if self.prom_31_0 + self.prom_31_1 + self.prom_31_2 > 1:
                                choice = self.own
                                if self.cand_has_0 != 0 or self.cand_has_1 != 0 or self.cand_has_2 != 0 or self.cand_has_3 != 0 or self.cand_has_4 != 0 or self.cand_has_5 != 0 or self.cand_has_6 != 0 or self.cand_has_7 != 0 or self.cand_has_8 != 0 or self.cand_has_9 != 0 or self.cand_has_10 != 0 or self.cand_has_11 != 0 or self.cand_has_12 != 0 or self.cand_has_13 != 0 or self.cand_has_14 != 0 or self.cand_has_15 != 0 or self.cand_has_16 != 0 or self.cand_has_17 != 0 or self.cand_has_18 != 0 or self.cand_has_19 != 0 or self.cand_has_20 != 0 or self.cand_has_21 != 0 or self.cand_has_22 != 0 or self.cand_has_23 != 0 or self.cand_has_24 != 0 or self.cand_has_25 != 0 or self.cand_has_26 != 0 or self.cand_has_27 != 0 or self.cand_has_28 != 0 or self.cand_has_29 != 0 or self.cand_has_30 != 0 or self.cand_has_31 != 0:
                                    if self.cand_has_31 == 0:
                                        self.status = 1
                                        self.fault = 1
                                    else:
                                        best_count = self.num - self.num
                                        best_rank = self.num - self.num + 6
                                        if self.count_31_1 > best_count or (self.count_31_1 == best_count and self.count_31_1 != 0 and self.rank_31_1 < best_rank):
                                            best_count = self.count_31_1
                                            best_rank = self.rank_31_1
                                            choice = self.num - self.num + 1
                                        if self.count_31_2 > best_count or (self.count_31_2 == best_count and self.count_31_2 != 0 and self.rank_31_2 < best_rank):
                                            best_count = self.count_31_2
                                            best_rank = self.rank_31_2
                                            choice = self.num - self.num + 2
                                        if self.count_31_3 > best_count or (self.count_31_3 == best_count and self.count_31_3 != 0 and self.rank_31_3 < best_rank):
                                            best_count = self.count_31_3
                                            best_rank = self.rank_31_3
                                            choice = self.num - self.num + 3
                                        if self.count_31_4 > best_count or (self.count_31_4 == best_count and self.count_31_4 != 0 and self.rank_31_4 < best_rank):
                                            best_count = self.count_31_4
                                            best_rank = self.rank_31_4
                                            choice = self.num - self.num + 4
                                        if self.count_31_5 > best_count or (self.count_31_5 == best_count and self.count_31_5 != 0 and self.rank_31_5 < best_rank):
                                            best_count = self.count_31_5
                                            best_rank = self.rank_31_5
                                            choice = self.num - self.num + 5
                                        if best_count == 0:
                                            self.status = 1
                                            self.fault = 2
                                if self.status == 0:
                                    self.pv_has_31 = 1
                                    self.pv_31 = choice
                                    self.out_kind = 12
                                    self.out_target = -1
                                    self.out_num = number
                                    self.out_value = choice
                                    self.out_prior_n = -1
                                    self.out_prior_v = 0
                                    self.pc = 1
                elif event == 13:
                    self.num = max(self.num, number)
                    if number == 0:
                        self.acc_has_0 = 1
                        if sender == 0:
                            self.acc_0_0 = 1
                        if sender == 1:
                            self.acc_0_1 = 1
                        if sender == 2:
                            self.acc_0_2 = 1
                        if self.acc_0_0 + self.acc_0_1 + self.acc_0_2 > 1 and self.accepted == 0:
                            if self.pv_has_0 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_0
                                self.accepted = value
                    if number == 1:
                        self.acc_has_1 = 1
                        if sender == 0:
                            self.acc_1_0 = 1
                        if sender == 1:
                            self.acc_1_1 = 1
                        if sender == 2:
                            self.acc_1_2 = 1
                        if self.acc_1_0 + self.acc_1_1 + self.acc_1_2 > 1 and self.accepted == 0:
                            if self.pv_has_1 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_1
                                self.accepted = value
                    if number == 2:
                        self.acc_has_2 = 1
                        if sender == 0:
                            self.acc_2_0 = 1
                        if sender == 1:
                            self.acc_2_1 = 1
                        if sender == 2:
                            self.acc_2_2 = 1
                        if self.acc_2_0 + self.acc_2_1 + self.acc_2_2 > 1 and self.accepted == 0:
                            if self.pv_has_2 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_2
                                self.accepted = value
                    if number == 3:
                        self.acc_has_3 = 1
                        if sender == 0:
                            self.acc_3_0 = 1
                        if sender == 1:
                            self.acc_3_1 = 1
                        if sender == 2:
                            self.acc_3_2 = 1
                        if self.acc_3_0 + self.acc_3_1 + self.acc_3_2 > 1 and self.accepted == 0:
                            if self.pv_has_3 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_3
                                self.accepted = value
                    if number == 4:
                        self.acc_has_4 = 1
                        if sender == 0:
                            self.acc_4_0 = 1
                        if sender == 1:
                            self.acc_4_1 = 1
                        if sender == 2:
                            self.acc_4_2 = 1
                        if self.acc_4_0 + self.acc_4_1 + self.acc_4_2 > 1 and self.accepted == 0:
                            if self.pv_has_4 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_4
                                self.accepted = value
                    if number == 5:
                        self.acc_has_5 = 1
                        if sender == 0:
                            self.acc_5_0 = 1
                        if sender == 1:
                            self.acc_5_1 = 1
                        if sender == 2:
                            self.acc_5_2 = 1
                        if self.acc_5_0 + self.acc_5_1 + self.acc_5_2 > 1 and self.accepted == 0:
                            if self.pv_has_5 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_5
                                self.accepted = value
                    if number == 6:
                        self.acc_has_6 = 1
                        if sender == 0:
                            self.acc_6_0 = 1
                        if sender == 1:
                            self.acc_6_1 = 1
                        if sender == 2:
                            self.acc_6_2 = 1
                        if self.acc_6_0 + self.acc_6_1 + self.acc_6_2 > 1 and self.accepted == 0:
                            if self.pv_has_6 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_6
                                self.accepted = value
                    if number == 7:
                        self.acc_has_7 = 1
                        if sender == 0:
                            self.acc_7_0 = 1
                        if sender == 1:
                            self.acc_7_1 = 1
                        if sender == 2:
                            self.acc_7_2 = 1
                        if self.acc_7_0 + self.acc_7_1 + self.acc_7_2 > 1 and self.accepted == 0:
                            if self.pv_has_7 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_7
                                self.accepted = value
                    if number == 8:
                        self.acc_has_8 = 1
                        if sender == 0:
                            self.acc_8_0 = 1
                        if sender == 1:
                            self.acc_8_1 = 1
                        if sender == 2:
                            self.acc_8_2 = 1
                        if self.acc_8_0 + self.acc_8_1 + self.acc_8_2 > 1 and self.accepted == 0:
                            if self.pv_has_8 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_8
                                self.accepted = value
                    if number == 9:
                        self.acc_has_9 = 1
                        if sender == 0:
                            self.acc_9_0 = 1
                        if sender == 1:
                            self.acc_9_1 = 1
                        if sender == 2:
                            self.acc_9_2 = 1
                        if self.acc_9_0 + self.acc_9_1 + self.acc_9_2 > 1 and self.accepted == 0:
                            if self.pv_has_9 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_9
                                self.accepted = value
                    if number == 10:
                        self.acc_has_10 = 1
                        if sender == 0:
                            self.acc_10_0 = 1
                        if sender == 1:
                            self.acc_10_1 = 1
                        if sender == 2:
                            self.acc_10_2 = 1
                        if self.acc_10_0 + self.acc_10_1 + self.acc_10_2 > 1 and self.accepted == 0:
                            if self.pv_has_10 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_10
                                self.accepted = value
                    if number == 11:
                        self.acc_has_11 = 1
                        if sender == 0:
                            self.acc_11_0 = 1
                        if sender == 1:
                            self.acc_11_1 = 1
                        if sender == 2:
                            self.acc_11_2 = 1
                        if self.acc_11_0 + self.acc_11_1 + self.acc_11_2 > 1 and self.accepted == 0:
                            if self.pv_has_11 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_11
                                self.accepted = value
                    if number == 12:
                        self.acc_has_12 = 1
                        if sender == 0:
                            self.acc_12_0 = 1
                        if sender == 1:
                            self.acc_12_1 = 1
                        if sender == 2:
                            self.acc_12_2 = 1
                        if self.acc_12_0 + self.acc_12_1 + self.acc_12_2 > 1 and self.accepted == 0:
                            if self.pv_has_12 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_12
                                self.accepted = value
                    if number == 13:
                        self.acc_has_13 = 1
                        if sender == 0:
                            self.acc_13_0 = 1
                        if sender == 1:
                            self.acc_13_1 = 1
                        if sender == 2:
                            self.acc_13_2 = 1
                        if self.acc_13_0 + self.acc_13_1 + self.acc_13_2 > 1 and self.accepted == 0:
                            if self.pv_has_13 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_13
                                self.accepted = value
                    if number == 14:
                        self.acc_has_14 = 1
                        if sender == 0:
                            self.acc_14_0 = 1
                        if sender == 1:
                            self.acc_14_1 = 1
                        if sender == 2:
                            self.acc_14_2 = 1
                        if self.acc_14_0 + self.acc_14_1 + self.acc_14_2 > 1 and self.accepted == 0:
                            if self.pv_has_14 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_14
                                self.accepted = value
                    if number == 15:
                        self.acc_has_15 = 1
                        if sender == 0:
                            self.acc_15_0 = 1
                        if sender == 1:
                            self.acc_15_1 = 1
                        if sender == 2:
                            self.acc_15_2 = 1
                        if self.acc_15_0 + self.acc_15_1 + self.acc_15_2 > 1 and self.accepted == 0:
                            if self.pv_has_15 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_15
                                self.accepted = value
                    if number == 16:
                        self.acc_has_16 = 1
                        if sender == 0:
                            self.acc_16_0 = 1
                        if sender == 1:
                            self.acc_16_1 = 1
                        if sender == 2:
                            self.acc_16_2 = 1
                        if self.acc_16_0 + self.acc_16_1 + self.acc_16_2 > 1 and self.accepted == 0:
                            if self.pv_has_16 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_16
                                self.accepted = value
                    if number == 17:
                        self.acc_has_17 = 1
                        if sender == 0:
                            self.acc_17_0 = 1
                        if sender == 1:
                            self.acc_17_1 = 1
                        if sender == 2:
                            self.acc_17_2 = 1
                        if self.acc_17_0 + self.acc_17_1 + self.acc_17_2 > 1 and self.accepted == 0:
                            if self.pv_has_17 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_17
                                self.accepted = value
                    if number == 18:
                        self.acc_has_18 = 1
                        if sender == 0:
                            self.acc_18_0 = 1
                        if sender == 1:
                            self.acc_18_1 = 1
                        if sender == 2:
                            self.acc_18_2 = 1
                        if self.acc_18_0 + self.acc_18_1 + self.acc_18_2 > 1 and self.accepted == 0:
                            if self.pv_has_18 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_18
                                self.accepted = value
                    if number == 19:
                        self.acc_has_19 = 1
                        if sender == 0:
                            self.acc_19_0 = 1
                        if sender == 1:
                            self.acc_19_1 = 1
                        if sender == 2:
                            self.acc_19_2 = 1
                        if self.acc_19_0 + self.acc_19_1 + self.acc_19_2 > 1 and self.accepted == 0:
                            if self.pv_has_19 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_19
                                self.accepted = value
                    if number == 20:
                        self.acc_has_20 = 1
                        if sender == 0:
                            self.acc_20_0 = 1
                        if sender == 1:
                            self.acc_20_1 = 1
                        if sender == 2:
                            self.acc_20_2 = 1
                        if self.acc_20_0 + self.acc_20_1 + self.acc_20_2 > 1 and self.accepted == 0:
                            if self.pv_has_20 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_20
                                self.accepted = value
                    if number == 21:
                        self.acc_has_21 = 1
                        if sender == 0:
                            self.acc_21_0 = 1
                        if sender == 1:
                            self.acc_21_1 = 1
                        if sender == 2:
                            self.acc_21_2 = 1
                        if self.acc_21_0 + self.acc_21_1 + self.acc_21_2 > 1 and self.accepted == 0:
                            if self.pv_has_21 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_21
                                self.accepted = value
                    if number == 22:
                        self.acc_has_22 = 1
                        if sender == 0:
                            self.acc_22_0 = 1
                        if sender == 1:
                            self.acc_22_1 = 1
                        if sender == 2:
                            self.acc_22_2 = 1
                        if self.acc_22_0 + self.acc_22_1 + self.acc_22_2 > 1 and self.accepted == 0:
                            if self.pv_has_22 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_22
                                self.accepted = value
                    if number == 23:
                        self.acc_has_23 = 1
                        if sender == 0:
                            self.acc_23_0 = 1
                        if sender == 1:
                            self.acc_23_1 = 1
                        if sender == 2:
                            self.acc_23_2 = 1
                        if self.acc_23_0 + self.acc_23_1 + self.acc_23_2 > 1 and self.accepted == 0:
                            if self.pv_has_23 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_23
                                self.accepted = value
                    if number == 24:
                        self.acc_has_24 = 1
                        if sender == 0:
                            self.acc_24_0 = 1
                        if sender == 1:
                            self.acc_24_1 = 1
                        if sender == 2:
                            self.acc_24_2 = 1
                        if self.acc_24_0 + self.acc_24_1 + self.acc_24_2 > 1 and self.accepted == 0:
                            if self.pv_has_24 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_24
                                self.accepted = value
                    if number == 25:
                        self.acc_has_25 = 1
                        if sender == 0:
                            self.acc_25_0 = 1
                        if sender == 1:
                            self.acc_25_1 = 1
                        if sender == 2:
                            self.acc_25_2 = 1
                        if self.acc_25_0 + self.acc_25_1 + self.acc_25_2 > 1 and self.accepted == 0:
                            if self.pv_has_25 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_25
                                self.accepted = value
                    if number == 26:
                        self.acc_has_26 = 1
                        if sender == 0:
                            self.acc_26_0 = 1
                        if sender == 1:
                            self.acc_26_1 = 1
                        if sender == 2:
                            self.acc_26_2 = 1
                        if self.acc_26_0 + self.acc_26_1 + self.acc_26_2 > 1 and self.accepted == 0:
                            if self.pv_has_26 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_26
                                self.accepted = value
                    if number == 27:
                        self.acc_has_27 = 1
                        if sender == 0:
                            self.acc_27_0 = 1
                        if sender == 1:
                            self.acc_27_1 = 1
                        if sender == 2:
                            self.acc_27_2 = 1
                        if self.acc_27_0 + self.acc_27_1 + self.acc_27_2 > 1 and self.accepted == 0:
                            if self.pv_has_27 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_27
                                self.accepted = value
                    if number == 28:
                        self.acc_has_28 = 1
                        if sender == 0:
                            self.acc_28_0 = 1
                        if sender == 1:
                            self.acc_28_1 = 1
                        if sender == 2:
                            self.acc_28_2 = 1
                        if self.acc_28_0 + self.acc_28_1 + self.acc_28_2 > 1 and self.accepted == 0:
                            if self.pv_has_28 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_28
                                self.accepted = value
                    if number == 29:
                        self.acc_has_29 = 1
                        if sender == 0:
                            self.acc_29_0 = 1
                        if sender == 1:
                            self.acc_29_1 = 1
                        if sender == 2:
                            self.acc_29_2 = 1
                        if self.acc_29_0 + self.acc_29_1 + self.acc_29_2 > 1 and self.accepted == 0:
                            if self.pv_has_29 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_29
                                self.accepted = value
                    if number == 30:
                        self.acc_has_30 = 1
                        if sender == 0:
                            self.acc_30_0 = 1
                        if sender == 1:
                            self.acc_30_1 = 1
                        if sender == 2:
                            self.acc_30_2 = 1
                        if self.acc_30_0 + self.acc_30_1 + self.acc_30_2 > 1 and self.accepted == 0:
                            if self.pv_has_30 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_30
                                self.accepted = value
                    if number == 31:
                        self.acc_has_31 = 1
                        if sender == 0:
                            self.acc_31_0 = 1
                        if sender == 1:
                            self.acc_31_1 = 1
                        if sender == 2:
                            self.acc_31_2 = 1
                        if self.acc_31_0 + self.acc_31_1 + self.acc_31_2 > 1 and self.accepted == 0:
                            if self.pv_has_31 == 0:
                                self.status = 1
                                self.fault = 1
                            else:
                                self.declared = 1
                                self.declared_num = number
                                self.declared_value = self.pv_31
                                self.accepted = value
        if self.num > 31 or self.out_num > 31 or number > 31:
            self.status = 2
        if value < 0 or value >= 6 or prior_value < 0 or prior_value >= 6 or sender < 0 or sender >= 3:
            self.status = 2
        if self.count_0_1 > 31 or self.count_0_2 > 31 or self.count_0_3 > 31 or self.count_0_4 > 31 or self.count_0_5 > 31:
            self.status = 2
        if self.count_1_1 > 31 or self.count_1_2 > 31 or self.count_1_3 > 31 or self.count_1_4 > 31 or self.count_1_5 > 31:
            self.status = 2
        if self.count_2_1 > 31 or self.count_2_2 > 31 or self.count_2_3 > 31 or self.count_2_4 > 31 or self.count_2_5 > 31:
            self.status = 2
        if self.count_3_1 > 31 or self.count_3_2 > 31 or self.count_3_3 > 31 or self.count_3_4 > 31 or self.count_3_5 > 31:
            self.status = 2
        if self.count_4_1 > 31 or self.count_4_2 > 31 or self.count_4_3 > 31 or self.count_4_4 > 31 or self.count_4_5 > 31:
            self.status = 2
        if self.count_5_1 > 31 or self.count_5_2 > 31 or self.count_5_3 > 31 or self.count_5_4 > 31 or self.count_5_5 > 31:
            self.status = 2
        if self.count_6_1 > 31 or self.count_6_2 > 31 or self.count_6_3 > 31 or self.count_6_4 > 31 or self.count_6_5 > 31:
            self.status = 2
        if self.count_7_1 > 31 or self.count_7_2 > 31 or self.count_7_3 > 31 or self.count_7_4 > 31 or self.count_7_5 > 31:
            self.status = 2
        if self.count_8_1 > 31 or self.count_8_2 > 31 or self.count_8_3 > 31 or self.count_8_4 > 31 or self.count_8_5 > 31:
            self.status = 2
        if self.count_9_1 > 31 or self.count_9_2 > 31 or self.count_9_3 > 31 or self.count_9_4 > 31 or self.count_9_5 > 31:
            self.status = 2
        if self.count_10_1 > 31 or self.count_10_2 > 31 or self.count_10_3 > 31 or self.count_10_4 > 31 or self.count_10_5 > 31:
            self.status = 2
        if self.count_11_1 > 31 or self.count_11_2 > 31 or self.count_11_3 > 31 or self.count_11_4 > 31 or self.count_11_5 > 31:
            self.status = 2
        if self.count_12_1 > 31 or self.count_12_2 > 31 or self.count_12_3 > 31 or self.count_12_4 > 31 or self.count_12_5 > 31:
            self.status = 2
        if self.count_13_1 > 31 or self.count_13_2 > 31 or self.count_13_3 > 31 or self.count_13_4 > 31 or self.count_13_5 > 31:
            self.status = 2
        if self.count_14_1 > 31 or self.count_14_2 > 31 or self.count_14_3 > 31 or self.count_14_4 > 31 or self.count_14_5 > 31:
            self.status = 2
        if self.count_15_1 > 31 or self.count_15_2 > 31 or self.count_15_3 > 31 or self.count_15_4 > 31 or self.count_15_5 > 31:
            self.status = 2
        if self.count_16_1 > 31 or self.count_16_2 > 31 or self.count_16_3 > 31 or self.count_16_4 > 31 or self.count_16_5 > 31:
            self.status = 2
        if self.count_17_1 > 31 or self.count_17_2 > 31 or self.count_17_3 > 31 or self.count_17_4 > 31 or self.count_17_5 > 31:
            self.status = 2
        if self.count_18_1 > 31 or self.count_18_2 > 31 or self.count_18_3 > 31 or self.count_18_4 > 31 or self.count_18_5 > 31:
            self.status = 2
        if self.count_19_1 > 31 or self.count_19_2 > 31 or self.count_19_3 > 31 or self.count_19_4 > 31 or self.count_19_5 > 31:
            self.status = 2
        if self.count_20_1 > 31 or self.count_20_2 > 31 or self.count_20_3 > 31 or self.count_20_4 > 31 or self.count_20_5 > 31:
            self.status = 2
        if self.count_21_1 > 31 or self.count_21_2 > 31 or self.count_21_3 > 31 or self.count_21_4 > 31 or self.count_21_5 > 31:
            self.status = 2
        if self.count_22_1 > 31 or self.count_22_2 > 31 or self.count_22_3 > 31 or self.count_22_4 > 31 or self.count_22_5 > 31:
            self.status = 2
        if self.count_23_1 > 31 or self.count_23_2 > 31 or self.count_23_3 > 31 or self.count_23_4 > 31 or self.count_23_5 > 31:
            self.status = 2
        if self.count_24_1 > 31 or self.count_24_2 > 31 or self.count_24_3 > 31 or self.count_24_4 > 31 or self.count_24_5 > 31:
            self.status = 2
        if self.count_25_1 > 31 or self.count_25_2 > 31 or self.count_25_3 > 31 or self.count_25_4 > 31 or self.count_25_5 > 31:
            self.status = 2
        if self.count_26_1 > 31 or self.count_26_2 > 31 or self.count_26_3 > 31 or self.count_26_4 > 31 or self.count_26_5 > 31:
            self.status = 2
        if self.count_27_1 > 31 or self.count_27_2 > 31 or self.count_27_3 > 31 or self.count_27_4 > 31 or self.count_27_5 > 31:
            self.status = 2
        if self.count_28_1 > 31 or self.count_28_2 > 31 or self.count_28_3 > 31 or self.count_28_4 > 31 or self.count_28_5 > 31:
            self.status = 2
        if self.count_29_1 > 31 or self.count_29_2 > 31 or self.count_29_3 > 31 or self.count_29_4 > 31 or self.count_29_5 > 31:
            self.status = 2
        if self.count_30_1 > 31 or self.count_30_2 > 31 or self.count_30_3 > 31 or self.count_30_4 > 31 or self.count_30_5 > 31:
            self.status = 2
        if self.count_31_1 > 31 or self.count_31_2 > 31 or self.count_31_3 > 31 or self.count_31_4 > 31 or self.count_31_5 > 31:
            self.status = 2
        return 0
