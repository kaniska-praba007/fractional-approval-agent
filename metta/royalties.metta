;; ==============================================================================
;; Fractional Approval Agent - Fiduciary Settlement & Royalty Rules
;; Implementation Contract: docs/CONTEXT.md Section 6
;; Strictly integer minor units (cents) and basis points (bps).
;; ==============================================================================

;; --- Recursive Cap Table Split & Payout Accumulation ---
;; Evaluates payouts for each co-owner in fixed cap-table order:
;; share = (/ (* pool bps) 10000)
(= (calc-shares $pool ()) ())
(= (calc-shares $pool (cons-share (share-entry $owner $bps $wallet) $rest))
   (cons-payout (payout-entry $owner $bps $wallet (/ (* $pool $bps) 10000))
                (calc-shares $pool $rest)))

;; --- Sum Distributed Co-Owner Shares ---
(= (sum-shares ()) 0)
(= (sum-shares (cons-payout (payout-entry $owner $bps $wallet $amt) $rest))
   (+ $amt (sum-shares $rest)))

;; --- Core Fiduciary Settlement Calculation ---
;; Order of deduction (CONTEXT Section 6):
;; 1. platform-fee = (/ (* gross fee-bps) 10000)
;; 2. net = (- gross platform-fee)
;; 3. artist-royalty = (/ (* net royalty-bps) 10000)
;; 4. community-cut = (/ (* net community-bps) 10000)
;; 5. pool = (- (- net artist-royalty) community-cut)
;; 6. co-owner-shares = (calc-shares pool cap-table)
;; 7. dust = (- pool (sum-shares co-owner-shares)) -> deterministically swept to community
;; 8. community-total = (+ community-cut dust)
;; 9. conservation proof: fee + artist + community + sum(shares) + dust == gross
(= (execute-settlement $artwork $gross $fee-bps $royalty-bps $community-bps $cap)
   (let* (($fee (/ (* $gross $fee-bps) 10000))
          ($net (- $gross $fee))
          ($artist (/ (* $net $royalty-bps) 10000))
          ($comm (/ (* $net $community-bps) 10000))
          ($pool (- (- $net $artist) $comm))
          ($shares (calc-shares $pool $cap))
          ($shares-sum (sum-shares $shares))
          ($dust (- $pool $shares-sum))
          ($comm-total (+ $comm $dust))
          ($total-dist (+ $fee (+ $artist (+ $comm (+ $shares-sum $dust)))))
          ($conserved (== $total-dist $gross)))
      (proof $artwork $gross $fee $net $artist $comm $dust $comm-total $shares $conserved $pool)))

;; --- Standard Resale Policy Evaluation ---
;; Queries AtomSpace for artwork facts and validates fiduciary boundaries.
(= (evaluate-resale $artwork $gross $currency $result)
   (match &self (, (artwork-reserve $artwork $reserve $curr)
                   (artwork-royalty $artwork $royalty-bps $floor-bps)
                   (artwork-community $artwork $comm-bps $comm-wallet)
                   (artwork-fee $artwork $fee-bps)
                   (artwork-status $artwork $status)
                   (artwork-cap $artwork $cap))
      (if (not (== $currency $curr))
          (rejected UNSUPPORTED_CURRENCY $currency $curr)
          (if (< $gross $reserve)
              (rejected BELOW_RESERVE $gross $reserve)
              (if (== $status CONTESTED)
                  (rejected ARTWORK_CONTESTED $status)
                  (execute-settlement $artwork $gross $fee-bps $royalty-bps $comm-bps $cap))))))

;; --- Resale Policy Evaluation with Manager Royalty Override ---
;; Overrides are bounded: must not lower royalty below statutory floor covenant.
(= (evaluate-resale-override-royalty $artwork $gross $currency $override-royalty $result)
   (match &self (, (artwork-reserve $artwork $reserve $curr)
                   (artwork-royalty $artwork $stored-royalty $floor-bps)
                   (artwork-community $artwork $comm-bps $comm-wallet)
                   (artwork-fee $artwork $fee-bps)
                   (artwork-status $artwork $status)
                   (artwork-cap $artwork $cap))
      (if (not (== $currency $curr))
          (rejected UNSUPPORTED_CURRENCY $currency $curr)
          (if (< $gross $reserve)
              (rejected BELOW_RESERVE $gross $reserve)
              (if (< $override-royalty $floor-bps)
                  (rejected OVERRIDE_BELOW_FLOOR $override-royalty $floor-bps)
                  (if (== $status CONTESTED)
                      (rejected ARTWORK_CONTESTED $status)
                      (execute-settlement $artwork $gross $fee-bps $override-royalty $comm-bps $cap)))))))

;; --- Resale Policy Evaluation with Manager Community Override ---
;; Overrides cannot decrease community contribution.
(= (evaluate-resale-override-community $artwork $gross $currency $override-comm $result)
   (match &self (, (artwork-reserve $artwork $reserve $curr)
                   (artwork-royalty $artwork $royalty-bps $floor-bps)
                   (artwork-community $artwork $stored-comm $comm-wallet)
                   (artwork-fee $artwork $fee-bps)
                   (artwork-status $artwork $status)
                   (artwork-cap $artwork $cap))
      (if (not (== $currency $curr))
          (rejected UNSUPPORTED_CURRENCY $currency $curr)
          (if (< $gross $reserve)
              (rejected BELOW_RESERVE $gross $reserve)
              (if (< $override-comm $stored-comm)
                  (rejected OVERRIDE_NOT_ALLOWED $override-comm $stored-comm)
                  (if (== $status CONTESTED)
                      (rejected ARTWORK_CONTESTED $status)
                      (execute-settlement $artwork $gross $fee-bps $royalty-bps $override-comm $cap)))))))
