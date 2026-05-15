name: Bug Report
description: Report a problem in eCOS
labels: [bug]
body:
  - type: textarea
    attributes:
      label: Description
      description: What happened?
    validations:
      required: true
  - type: textarea
    attributes:
      label: Steps to Reproduce
      description: How can we reproduce this?
  - type: dropdown
    attributes:
      label: Severity
      options: [LOW, MED, HIGH, CRITICAL]
  - type: textarea
    attributes:
      label: System State
      description: Paste STATE.yaml summary if available
