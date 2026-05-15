name: Feature Request
description: Propose a new feature for eCOS
labels: [enhancement]
body:
  - type: textarea
    attributes:
      label: Proposal
      description: What feature do you want?
    validations:
      required: true
  - type: dropdown
    attributes:
      label: Layer (六层架构)
      options: [L1宪法, L2感知, L3持久, L4智能, L5行动, L6反馈]
  - type: textarea
    attributes:
      label: Implementation Constraint Check
      description: Run pre_design_check.py and paste results
