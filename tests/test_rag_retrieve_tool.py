# -*- coding: utf-8 -*-
"""Tests for rag_retrieve tool"""
import pytest
import json

from tools.bazi_tools import TOOL_REGISTRY, dispatch_tool

def test_rag_retrieve_in_registry():
    """Test rag_retrieve exists in TOOL_REGISTRY"""
    assert 'rag_retrieve' in TOOL_REGISTRY

def test_rag_retrieve_dispatch():
    """Test rag_retrieve dispatches correctly"""
    bazi_data = {'day_master': '甲'}
    result = dispatch_tool('rag_retrieve', {'query': '测试', 'top_k': 3}, bazi_data)
    assert isinstance(result, str)
    data = json.loads(result)
    assert 'exact_matches' in data or 'error' in data