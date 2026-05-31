# -*- coding: utf-8 -*-
"""Tests for ScholarAgent"""
import pytest

from agent.scholar_agent import ScholarAgent

def test_scholar_agent_init():
    """Test ScholarAgent initializes with services"""
    sa = ScholarAgent()
    assert sa.text_service is not None
    assert sa.rag_service is not None

def test_scholar_agent_retrieve_knowledge():
    """Test retrieve_knowledge returns JSON string"""
    sa = ScholarAgent()
    chart_data = {'day_master': '甲', 'pillars': [['甲子', '甲寅'], ['甲辰', '甲申']]}
    result = sa.retrieve_knowledge(chart_data, '测试问题')
    assert isinstance(result, str)
    assert 'exact_matches' in result