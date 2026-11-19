# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

from collections.abc import Iterable, Mapping
from typing import Any, Optional

from ansible.module_utils.basic import AnsibleModule


def leaf_values(value: Any) -> Iterable[str]:
    """Yield every scalar contained in ``value`` as a string.

    This mirrors how ansible-core collects ``no_log`` values: mappings
    contribute their values (never their keys), sequences are walked and
    scalars are stringified. ``bool`` and ``None`` are skipped because
    masking them would corrupt unrelated output.
    """
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, str):
        if value:
            yield value
        return
    if isinstance(value, Mapping):
        for item in value.values():
            yield from leaf_values(item)
        return
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            yield from leaf_values(item)
        return
    if isinstance(value, (int, float)):
        yield str(value)


def protect_dict_values(
    module: AnsibleModule,
    param_name: str,
    sensitive_fields: Optional[Iterable[str]] = None,
) -> set[str]:
    """Register the values of a dict parameter as ``no_log``.

    ansible-core collects ``no_log`` values before coercing a parameter to
    its declared type, so a dict supplied as a JSON/k=v string is never
    registered and its values are printed in clear text. Calling this after
    ``AnsibleModule`` initialization re-registers the coerced values.

    ``sensitive_fields`` selects which keys carry secrets. ``None`` means the
    caller cannot establish that, in which case every value is registered
    (fail closed).

    The parameter is expected to be declared with ``no_log=True`` so that
    ``AnsibleModule.__init__`` already masks it in the invocation log
    (journald/syslog). That blanket registration is replaced here so task
    output only hides the values that actually need hiding.

    Returns the values that are now registered for this parameter.
    """
    values = module.params.get(param_name)
    if values is None:
        return set()

    if not isinstance(values, Mapping):
        # Should not happen for type="dict", but never leave a raw value
        # unprotected.
        masked = set(leaf_values(values))
        module.no_log_values.update(masked)
        return masked

    if sensitive_fields is None:
        masked = set(leaf_values(values))
    else:
        masked = set()
        for field in sensitive_fields:
            if field in values:
                masked.update(leaf_values(values[field]))

    if module.argument_spec.get(param_name, {}).get("no_log"):
        # Undo the blanket registration performed during AnsibleModule
        # initialization, keeping values other no_log parameters rely on.
        blanket = set(leaf_values(values))
        module.no_log_values.difference_update(
            blanket - _other_no_log_values(module, param_name)
        )

    module.no_log_values.update(masked)
    return masked


def _other_no_log_values(module: AnsibleModule, param_name: str) -> set[str]:
    """Return the no_log values registered for every other parameter."""
    protected: set[str] = set()
    for name, spec in module.argument_spec.items():
        if name == param_name or not spec.get("no_log"):
            continue
        protected.update(leaf_values(module.params.get(name)))
    return protected
