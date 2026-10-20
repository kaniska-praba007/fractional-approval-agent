;; ==============================================================================
;; MeTTa Direct Unit Tests for metta/royalties.metta
;; Executed directly against pinned hyperon runtime
;; ==============================================================================

;; --- Load Synthetic Artwork Facts for Scenarios ---
;; HFA-101 (Synthetic Living Artist)
(artwork-reserve HFA-101 300000 USD)
(artwork-royalty HFA-101 1500 1000)
(artwork-community HFA-101 300 0xcommunity_fund)
(artwork-fee HFA-101 0)
(artwork-status HFA-101 LIVING)
(artwork-cap HFA-101 (cons-share (share-entry alice 6000 0xalice)
                     (cons-share (share-entry bob 4000 0xbob) ())))

;; HFA-102 (Synthetic Single-Owner)
(artwork-reserve HFA-102 500000 USD)
(artwork-royalty HFA-102 1200 1000)
(artwork-community HFA-102 300 0xcommunity_fund)
(artwork-fee HFA-102 0)
(artwork-status HFA-102 LIVING)
(artwork-cap HFA-102 (cons-share (share-entry charlie 10000 0xcharlie) ()))

;; HFA-103 (Synthetic Estate Managed)
(artwork-reserve HFA-103 4000000 USD)
(artwork-royalty HFA-103 1000 1000)
(artwork-community HFA-103 500 0xcommunity_fund)
(artwork-fee HFA-103 0)
(artwork-status HFA-103 ESTATE_MANAGED)
(artwork-cap HFA-103 (cons-share (share-entry dave 5000 0xdave)
                     (cons-share (share-entry elena 3000 0xelena)
                     (cons-share (share-entry frank 2000 0xfrank) ()))))

;; TEST-DUST (Synthetic Precision Benchmark)
(artwork-reserve TEST-DUST 1 USD)
(artwork-royalty TEST-DUST 0 0)
(artwork-community TEST-DUST 0 0xcommunity_fund)
(artwork-fee TEST-DUST 0)
(artwork-status TEST-DUST LIVING)
(artwork-cap TEST-DUST (cons-share (share-entry holder_a 3333 0xholder_a)
                       (cons-share (share-entry holder_b 3333 0xholder_b)
                       (cons-share (share-entry holder_c 3334 0xholder_c) ()))))

;; --- Assertions for SC-01 through SC-06 ---

;; Test SC-01: Standard Resale (HFA-101, gross 1000000)
!(assertEqual
  (evaluate-resale HFA-101 1000000 USD $result)
  (proof HFA-101 1000000 0 1000000 150000 30000 0 30000
    (cons-payout (payout-entry alice 6000 0xalice 492000)
    (cons-payout (payout-entry bob 4000 0xbob 328000) ()))
    True 820000))

;; Test SC-02: Below Reserve Rejection (HFA-101, gross 200000 < reserve 300000)
!(assertEqual
  (evaluate-resale HFA-101 200000 USD $result)
  (rejected BELOW_RESERVE 200000 300000))

;; Test SC-03: Prompt Injection Stored Rule Resistance (HFA-102, gross 600000)
!(assertEqual
  (evaluate-resale HFA-102 600000 USD $result)
  (proof HFA-102 600000 0 600000 72000 18000 0 18000
    (cons-payout (payout-entry charlie 10000 0xcharlie 510000) ())
    True 510000))

;; Test SC-04: Estate Manager Override Upward (HFA-103, override royalty 1200 bps)
!(assertEqual
  (evaluate-resale-override-royalty HFA-103 5000000 USD 1200 $result)
  (proof HFA-103 5000000 0 5000000 600000 250000 0 250000
    (cons-payout (payout-entry dave 5000 0xdave 2075000)
    (cons-payout (payout-entry elena 3000 0xelena 1245000)
    (cons-payout (payout-entry frank 2000 0xfrank 830000) ())))
    True 4150000))

;; Test SC-05: Override Below Floor Rejection (HFA-101, override 500 bps < floor 1000 bps)
!(assertEqual
  (evaluate-resale-override-royalty HFA-101 1000000 USD 500 $result)
  (rejected OVERRIDE_BELOW_FLOOR 500 1000))

;; Test SC-06: Dust Split Precision (TEST-DUST, gross 10001, dust 1 to community fund)
!(assertEqual
  (evaluate-resale TEST-DUST 10001 USD $result)
  (proof TEST-DUST 10001 0 10001 0 0 1 1
    (cons-payout (payout-entry holder_a 3333 0xholder_a 3333)
    (cons-payout (payout-entry holder_b 3333 0xholder_b 3333)
    (cons-payout (payout-entry holder_c 3334 0xholder_c 3334) ())))
    True 10001))
