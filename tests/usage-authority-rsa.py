#!/usr/bin/env python3
"""Verify independently generated RSA permit-signature fixtures offline."""
import base64
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import usage_telemetry_ingest as ingest

# Public test material only. The independently generated private key was discarded.
PUBLIC_KEY = b'''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxfsEriAFvZ33nsqe6oxR
Nmrm59J9onoTGOE/yjLt3ucP2zkaTj8RUQda6z1xxTlUjRKy3RXeOVPEWArFS5I/
75Ha1JtOj3xl4jd2lmsyQVi+Unt9CbCXdDS2JAF3HpQamvewM8+1LqHQNNtgiODZ
PnfmlhY+Oyv4OvcrvaO5eabvcHIqQFcIl2zVWkukv3l+9Rro4Ptjaq+Ere+tMQeu
ydUUEJ1ywFi+gL4wrdLyI7zoLzo12cWtFc2rcmNHn0mcDWMYehr5t7sOQxjVoeuu
W4pfgecUtKTn/UPbQqhVQfLH6Yi5Jm1MI4v+Ue9EKlv9lWL3oRf/goXAWP42rVoe
tQIDAQAB
-----END PUBLIC KEY-----
'''
MESSAGE = b'orchestrail:usage-authority:v1\0fixture'
SIGNATURE = bytes.fromhex(
    '65d738f29ca5a8b7b9afa71f0c30d5c5c4732a8318beda675fa0786f5bd2a0'
    'cb61a878b161eeac71d627819e8718e55e2a695f7e46d128c916f064aa6b163'
    '6248ec52ac0e464a6189b7960795f4dc01fbbcd3c801f63b5195397241c7ab'
    'ef66945aaa7dd74baa982cb449fa63c37cbbddfe5db0f6470d22dd374f8c14'
    'a96688032262180ffcbe010959d65f5b21dea6cab09f685f058014cb6eb6d8'
    'd7bbdcc9536b05ea501ce9ee31cea54318b55526c5df2c40e669e96a19b962'
    '5463f8a510f657708222824349b660ee3be1756759ed45820b2e61f3b3d7b'
    '61ea791ce1262fdabb9f19230b674c27cecb0251ce2269168097e873c5ea8'
    'd369de685d58bb310')
BAD_PADDING = bytes.fromhex(
    'c4e8d28095754bcaf5bcec66863c6d0f706fe6b80e8b4db2c2c9bfa221446a'
    '47c6734ee91e36e20e5a8de96c30957448cd3f488b5fcd586676e8a7db082'
    '10e26f4bb5798a24c2fb8d8160ad828d1997506ed75a90150d627355824ce'
    'c0540bc9b1227962c1f7ab2ca258afa0dca65f41d17503e27470e965b6930'
    'c925a658c697529d84065e8cfb5b4c8191919dffa569256872361d426bb21'
    '0d0dd54c73475154686623f5143af503397b1e6a1bf49f18999afb68c95f6'
    'a5934af84f0bde79bff5b16dd1be3feee444a314a26bdb9679c87f943d5cf'
    '84f63ea7e188d0cf11105c2d9a72a57d97050d590d4424609f2cc18dd7b68'
    'd140efb448ca9ceed6c4771')


class RsaAuthoritySignatureTests(unittest.TestCase):
    def verify(self, key=PUBLIC_KEY, message=MESSAGE, signature=SIGNATURE):
        return ingest.verify_rsa_sha256(key, message, signature)

    def test_independently_signed_fixture_is_accepted(self):
        self.assertTrue(self.verify())

    def test_signature_and_message_are_bound_exactly(self):
        for message, signature in ((MESSAGE + b'x', SIGNATURE),
                                   (MESSAGE, bytes([SIGNATURE[0] ^ 1]) + SIGNATURE[1:]),
                                   (MESSAGE, SIGNATURE[:-1]),
                                   (MESSAGE, b'\xff' * len(SIGNATURE))):
            with self.subTest(message=message, signature=signature[:4]):
                self.assertFalse(self.verify(message=message, signature=signature))

    def test_signed_noncanonical_padding_is_rejected(self):
        self.assertFalse(self.verify(signature=BAD_PADDING))

    def test_malformed_key_and_der_trailing_data_are_rejected(self):
        lines = PUBLIC_KEY.splitlines()
        der = base64.b64decode(b''.join(lines[1:-1]))
        bad_der = base64.b64encode(der + b'\x00')
        bad_key = b'-----BEGIN PUBLIC KEY-----\n' + bad_der + b'\n-----END PUBLIC KEY-----\n'
        for key in (b'', PUBLIC_KEY.replace(b'PUBLIC KEY', b'PRIVATE KEY'), bad_key):
            with self.subTest(key=key[:32]):
                self.assertFalse(self.verify(key=key))


if __name__ == '__main__':
    unittest.main()
