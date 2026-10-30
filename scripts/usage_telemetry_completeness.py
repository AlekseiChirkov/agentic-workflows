#!/usr/bin/env python3
"""Compute conservative coverage from independently verified inventory evidence.

The verifier is a trusted integration boundary: content hashes bind a declaration
but do not prove provenance, coverage, or an empty billable scope. Response facts
must already have passed identity, finality, measurement, and pricing resolution.
"""
import importlib.util
from pathlib import Path


_spec = importlib.util.spec_from_file_location(
    'usage_telemetry_contract', Path(__file__).resolve().with_name('usage_telemetry_contract.py'))
_contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_contract)


def _verified(inventory, evidence, scope, verifier):
    try:
        _contract.validate_inventory(inventory)
        if inventory['state'] == 'unknown' or inventory['owner_scope'] != scope:
            return False, False
        _contract.validate_evidence_object(evidence)
        declaration = {key: value for key, value in inventory.items() if key != 'evidence'}
        if (evidence.get('kind') != 'inventory_evidence'
                or evidence['profile_id'] != inventory['profile_id']
                or evidence['profile_version'] != inventory['profile_version']
                or evidence['source_hash'] != inventory['source_hash']
                or evidence['inventory_digest'] != _contract.content_id(declaration)
                or inventory['evidence'] != _contract.content_id(evidence)):
            return False, False
        result = verifier(inventory, evidence, scope)
        if not isinstance(result, dict) or result.get('inventory_verified') is not True:
            return False, False
        return True, result.get('billable_scope_empty') is True
    except (KeyError, TypeError, ValueError):
        return False, False


def _fraction(numerator, denominator, empty):
    if empty:
        return {'state': 'not_applicable', 'numerator': None, 'denominator': None}
    return {'numerator': numerator, 'denominator': denominator}


def calculate_completeness(inventory, evidence, responses, *, scope, verify_inventory, tool_costs):
    """Summarize finalized, resolved response facts within a verified scope.

    ``verify_inventory`` must check independent provenance and relevant coverage;
    its empty-billable assertion must include independent tool coverage. No values
    supplied in an inventory declaration can substitute for that verification.
    ``tool_costs`` contains separately verified applicable tool expenditures.
    """
    verified, billable_empty = _verified(inventory, evidence, scope, verify_inventory)
    if not isinstance(responses, list) or not isinstance(tool_costs, list):
        raise ValueError('invalid completeness input')

    unique = {}
    conflicts = set()
    for item in responses:
        if (not isinstance(item, dict) or set(item) != {'response_id', 'call_id', 'final', 'measurements', 'priced'}
                or not isinstance(item['response_id'], str)
                or not isinstance(item['call_id'], str)
                or type(item['final']) is not bool or type(item['priced']) is not bool
                or not isinstance(item['measurements'], dict)
                or set(item['measurements']) != {'input', 'output'}
                or any(type(value) is not bool for value in item['measurements'].values())):
            raise ValueError('invalid resolved response')
        identifier = item['response_id']
        if identifier in unique and unique[identifier] != item:
            conflicts.add(identifier)
        else:
            unique[identifier] = item

    complete = (verified and inventory['state'] == 'complete' and not inventory['unresolved_slots']
                and all(inventory['coverage'][dimension] == 'included'
                        for dimension in ('children', 'internal_checks')))
    expected = {item['response_id']: item['call_id'] for item in inventory.get('expected_responses', [])} if verified else {}
    if complete and any(key not in expected or expected[key] != item['call_id']
                        for key, item in unique.items()):
        complete = False
    if conflicts:
        complete = False
    denominator = len(expected) if complete else None
    counted = [item for key, item in unique.items() if key not in conflicts and
               (not verified or key in expected and expected[key] == item['call_id'])]
    finalized = [item for item in counted if item['final']]
    empty = complete and denominator == 0
    finality = _fraction(len(finalized), denominator, empty)
    measurements = {name: _fraction(sum(item['measurements'][name] for item in finalized), denominator, empty)
                    for name in ('input', 'output')}
    priced = _fraction(sum(item['priced'] for item in finalized), denominator, empty)
    zero_cost_proven = bool(empty and billable_empty and not unique and not tool_costs
                            and all(coverage == 'included' for coverage in inventory['coverage'].values()))
    return {'finality': finality, 'measurements': measurements, 'priced': priced,
            'zero_cost_proven': zero_cost_proven}
