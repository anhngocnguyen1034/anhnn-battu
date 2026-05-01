# -*- coding: utf-8 -*-
"""Tests for TextService"""
import pytest
import sys
sys.path.insert(0, 'C:/Users/Gaaiyun/Projects/FOR-BAZI/.worktrees/feature-rag')

from data.text_service import TextService

def test_text_service_query_with_source():
    """Test TextService query returns results for valid source"""
    ts = TextService()
    results = ts.query('滴天髓')
    assert isinstance(results, list)

def test_text_service_get_all_entries():
    """Test get_all_entries returns list of entries"""
    ts = TextService()
    entries = ts.get_all_entries('滴天髓')
    assert isinstance(entries, list)
    assert len(entries) > 0

def test_text_service_empty_source():
    """Test query with empty source returns empty"""
    ts = TextService()
    results = ts.query('')
    assert results == []