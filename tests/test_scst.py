from app.scst import scst_signal

def test_true():
    t = "अनुसूचित जातीच्या व्यक्तीला सार्वजनिक ठिकाणी जातिवाचक शिवीगाळ करून अपमान केला."
    r = scst_signal(t)
    assert r.is_scst is True

def test_missing_public():
    t = "अनुसूचित जातीच्या व्यक्तीला जातिवाचक शिवीगाळ करून अपमान केला."
    r = scst_signal(t)
    assert r.is_scst is False
    assert r.has_identity and r.has_abuse and (not r.has_public)

def test_missing_identity():
    t = "सार्वजनिक ठिकाणी शिवीगाळ करून अपमान केला."
    r = scst_signal(t)
    assert r.is_scst is False
    assert r.has_public and (not r.has_identity)