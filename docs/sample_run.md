
========================================================================
call_1_simple_auto_claim.txt
========================================================================
Hi, this is Maria Chen, policy number AUTO-10234. I was rear-ended at a stop
light yesterday afternoon. Minor damage to my rear bumper, nobody was hurt.
I'd like to file a claim to get it fixed.

--- agent trace ---
  [intake] intent='claim' caller_name='Maria Chen' policy_number='AUTO-10234'
  [verify_identity] policy AUTO-10234 on file for 'Maria Chen'; caller gave 'Maria Chen' -> verified=True
  [triage_claim] called check_claim_history({'policy_number': 'AUTO-10234'}) -> {'policy_number': 'AUTO-10234', 'prior_claims_count': 0, 'prior_fraud_flags': 0, 'policy_start_date': '2022-03-01'}
  [triage_claim] type='collision' severity='low' risk_flags=[]
  [resolve_claim] filed CLM-1000

--- decision: auto_resolved ---
Thank you for reporting this to us. Your collision claim has been filed under ticket number **CLM-1000**, and one of our claims adjusters will review the details and reach out to you within 1-2 business days to guide you through the next steps. We appreciate you taking the time to call, and we're here to help if you have any questions in the meantime!

========================================================================
call_2_coverage_question.txt
========================================================================
Hello, this is David Okafor, policy number HOME-58821. Before I start some
renovation work, I wanted to check what my water damage coverage limit and
deductible actually are on this policy.

--- agent trace ---
  [intake] intent='coverage_question' caller_name='David Okafor' policy_number='HOME-58821'
  [verify_identity] policy HOME-58821 on file for 'David Okafor'; caller gave 'David Okafor' -> verified=True
  [handle_inquiry] answered from policy record

--- decision: auto_resolved ---
Hi David — looking at your policy record HOME-58821, here's what I can confirm:

- **Overall coverage limit:** $350,000
- **Deductible:** $1,000

However, the record I have doesn't break out a separate sub-limit specifically for water damage — it only lists the overall dwelling coverage limit and the standard deductible. If your renovation involves plumbing, water lines, or areas prone to water exposure, I'd recommend asking about any specific water damage endorsements or exclusions (e.g., gradual leaks, flood, sewer backup are often handled differently or excluded under standard home policies). I don't have those details in this record, so I'd suggest confirming with underwriting or requesting your full policy declarations/endorsement page before starting the work.

========================================================================
call_3_suspicious_claim.txt
========================================================================
Hi, it's Priya Natarajan, policy AUTO-77410. My car was totaled in a garage
fire last night -- total loss. I need the full payout as soon as possible,
this is pretty urgent for me.

--- agent trace ---
  [intake] intent='claim' caller_name='Priya Natarajan' policy_number='AUTO-77410'
  [verify_identity] policy AUTO-77410 on file for 'Priya Natarajan'; caller gave 'Priya Natarajan' -> verified=True
  [triage_claim] called check_claim_history({'policy_number': 'AUTO-77410'}) -> {'policy_number': 'AUTO-77410', 'prior_claims_count': 3, 'prior_fraud_flags': 1, 'policy_start_date': '2024-11-02'}
  [triage_claim] type='fire' severity='high' risk_flags=['Policy has 3 prior claims', 'Policy has 1 prior fraud flag on record', 'Claimant is pressing for urgent full payout on a total-loss claim']
  [escalate] reason='risk flags from triage: Policy has 3 prior claims, Policy has 1 prior fraud flag on record, Claimant is pressing for urgent full payout on a total-loss claim'

--- decision: escalated ---
# Handoff Brief — Escalated Claim

**Escalation reason:** Triage flagged this claim for elevated fraud/risk review due to: (1) 3 prior claims on the policy, (2) 1 prior fraud flag already on record, and (3) claimant applying urgency pressure for immediate full payout on a total-loss claim. Combination of history + urgency + total loss warrants human review before any payout commitment.

**Caller/Policy details:**
- Caller: Priya Natarajan (identity verified)
- Policy: AUTO-77410, active, started 2024-11-02 (~under 1 year old)
- Coverage limit: $30,000 | Deductible: $250
- Prior claims: 3 | Prior fraud flag: 1 (details not in current record — needs lookup)

**Claim details:**
- Type: Fire (garage fire, overnight)
- Reported severity: High / total loss
- Claimant's ask: Full payout, urgently
- No supporting documentation, photos, fire department/incident report, or investigator assignment mentioned yet.

**What the human agent should check/ask first:**
1. Pull details on the prior fraud flag — what it was for, when, and whether it was substantiated or cleared.
2. Review the 3 prior claims — types, dates, payout amounts, and whether any pattern emerges (e.g., recurring total losses, similar circumstances).
3. Ask caller for: fire department incident report/case number, address where vehicle was stored, ownership/registration confirmation, and any photos of the damage.
4. Confirm whether a fire investigation has been opened (arson vs. accidental) — this is standard for any garage/vehicle fire and should be requested before payout.
5. Do NOT commit to a payout timeline or amount on this call. Explain that total-loss fire claims require standard investigation and documentation review, especially given policy history.
6. Consider flagging file for SIU (Special Investigations Unit) referral given the fraud flag + urgency pressure combination.
7. Set clear next steps and timeline expectations with the caller to manage the urgency without confirming payout.

========================================================================
call_4_unverifiable_caller.txt
========================================================================
Hi, um, I don't have my policy number handy, I think it starts with a G?
My name is Robert Smith and I need to report a claim on my car.

--- agent trace ---
  [intake] intent='claim' caller_name='Robert Smith' policy_number=None
  [verify_identity] no policy number captured -- cannot verify
  [escalate] reason='identity could not be verified'

--- decision: escalated ---
## Handoff Brief – Escalation: Identity Verification Failure

**Reason for Escalation:** Caller's identity could not be verified through standard authentication process.

**Caller Details:**
- Name given: Robert Smith
- Policy number: Unknown/not provided — caller believes it "starts with a G"
- Identity verification status: **Failed / Incomplete**

**Intent:** Caller wants to report a new auto claim.

**Claim Details:** None captured yet — call did not progress past identity verification.

**Risk Flags:** None raised yet, but note that identity is unconfirmed.

---

### What to check/ask first:
1. **Re-verify identity** using standard protocol — full name, DOB, address, and/or SSN (last 4), since policy number was unavailable.
2. **Search policy system** by name (Robert Smith) and partial policy prefix ("G...") to locate possible matches — flag if multiple accounts match this name.
3. Confirm caller has access to any other identifying info (email on file, phone number, VIN, etc.) to help locate the correct account.
4. If identity cannot be confirmed through available data, follow standard protocol for unverified callers — do **not** disclose or discuss any policy/claim details until verified.
5. Once verified, proceed to gather claim details (date/time of incident, vehicle involved, description of damage, other parties involved, police report if applicable).

**Caution:** Do not confirm or deny policy existence/details until identity is properly established, per standard privacy protocol.
