---
title: "2026-10-22 hardware findings"
created: 2026-10-22
status: observed
---

# Hardware findings

Physical tablet trials used the reported [equipment](../hardware/tablet.md).
Receive-only captures used explicit port /dev/ttyS0, 9600 8N1, flow control off,
and DTR/RTS requested off. Opening can affect control lines; electrical behavior
and cable pinout were not measured. No application command bytes were sent.

## Observed results

- E02: three-second stationary baseline received zero bytes, with no prescribed
  actions. Later button trials show why silence alone cannot identify a fault.
- E04–E28: 25 completed physical captures, 66,368 RX bytes. Hashes and event/raw
  reconstruction passed offline checks; all closes reported no cleanup errors.
- Nonempty captures have a high-bit first byte and four bytes with that bit clear.
  H, I and A puck captures retain respectively four, three and one leading bytes
  outside complete groups, consistent with opening mid-group.
- Four separate puck trials each gave three bursts. The instructed mapping is
  top-left 99, top-right 9A, bottom-left 9B, bottom-right 9C (hex). Complete
  physical-order confirmation was not separately recorded; combinations are unknown.
- Pen hover-only trial: zero bytes. Tip-only and side-button-only trials each
  gave three bursts, headed 99 and 9A respectively. The first mixed trial had
  operator-reported accidental presses and cannot establish action/header mapping.
  Header 9B as combined tip/side remains a hypothesis, not a verified result.

## Coordinate hypothesis

For zero-based group bytes, exploratory pairs are u=b1+128*b2 and v=b3+128*b4.
Nine puck targets support horizontal u increasing rightward and vertical v
increasing upward. A folded paper reference was only approximately 210 x 148 mm,
with 105 mm columns and 74 mm rows, placed in the tablet bottom-left region.
G is the paper bottom-left, not a measured active-area origin.

Median of three burst medians per target:

| Paper row | Left (u,v) | Middle (u,v) | Right (u,v) |
|---|---|---|---|
| Top | A (131,3010) | B (2111,2988) | C (4215,2970) |
| Middle | D (146,1547) | E (2200,1565) | F (4201,1568) |
| Bottom | G (113,156) | H (2136,167) | I (4185,163) |

The return to E gave (2175,1578), a change of (-25,+13) raw counts. This supports
absolute position reporting but cannot separate placement error from reference
movement or device drift. Short startup bursts count as readings, not full
two-second holds. No scale, physical accuracy, proximity threshold or pressure
capability is established, and no accepted calibration transform was fitted.

Pen tip-only readings near E broadly agreed with puck E. Pen G gave three
tip-only readings, summary (147,149), after excluding a separately headed 9A
burst following an operator-reported accidental side press. The mixed raw capture
remains unchanged. This does not measure tool offset. Exact action times and
reference precision were not independently measured.

## Provenance

Original captures remain local and unmodified, excluded from publication.
The table identifies session labels and SHA-256 evidence hashes; these establish
byte identity, not authenticity or rights. Detailed per-read notes remain in
the private research record. Trials were performed on 2026-10-22. No vendor
code was used to infer these measurements.

| Session | RX bytes | RX SHA-256 | Events SHA-256 |
|---|---|---|---|
| e02-puck-9600-8n1 | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | b0f244e2405ab75f90fe12f8f1c1324ccf7617bd223d97560a1f312731de2800 |
| e04-puck-motion-9600-8n1 | 590 | b2f6ecb035efb5d05ba0cd720ff74f3001009c6016df19d80c4745627bd674cc | d90f88820a8fe0a4c0d5a58f931ebb803120e8bc69fa726e51ed8ea32301ee81 |
| e05-puck-buttons-9600-8n1 | 3670 | 6b72821edc78f7deb58611c3313818140543b2972c9680e0c3b1331fcddd98e1 | 9968bde79ef65f903a5f3c96659fd5a75112e875b69e447a924fe1012fa88e28 |
| e06-puck-horizontal-9600-8n1 | 5065 | d6eb74559db427655f52c8a6724b0d1d5bab2e2eaf93ad2076482392ba86325a | 2f3fb2c3b921524429f6b36e2863bdfd6c4247cc9be93e385710cd543a2d1e2d |
| e07-puck-vertical-9600-8n1 | 5065 | b37f56d640d5d8c95d00692d29b97fa673fc0e57df855faaa7b247b874d59e55 | 0b6d5dc7a50d45c0acdc8b71c600b26a9a1874cea1bbde14665b790b1999d1d0 |
| e08-puck-center-top-left-9600-8n1 | 2885 | f667859469335faf3aed8746cc4436d8f7faa7511a7490044c55578d61cfb00a | 7e194d87ca6dbbe27bc1e2e353de05ff1611877219605b8c679f7caecad9f1eb |
| e09-puck-center-top-right-9600-8n1 | 2595 | 3e7f653760b538e7659f2bf29ed35121479e9e9c7523478ef172982bcf94f9ff | 72e7cceddc9aa98cf5ac311cf17aa17afe9381644ad054ab5727e26575896ec8 |
| e10-puck-center-bottom-left-9600-8n1 | 2485 | ea8adc23af758adba9100de054a7f8237d3bf532bf1ae9030c11f87291553fa6 | 2737751520ee4881c8d9032d8d6b3069b54bb6422d81b429fa8d956520b42f55 |
| e11-puck-center-bottom-right-9600-8n1 | 2210 | e0454f6791d14680fc9421571f8680a391430e6dac5b5a6e71f6558a6d953e7b | 7c4f6738e08c9f1b15c95890308c3e1a4ce841471fa1b8a41a630d3b7d530393 |
| e12-puck-grid-g-9600-8n1 | 1905 | d1b84cc9829a90017b2cad338ba96ed6af758be996fde76a04b850b91d7b6f86 | 3e5e8198f0eb14b8793c0ef93f9cd1091bc81c74fcef2c84c1c23ed3a9b1e00d |
| e13-puck-grid-g-repeat-9600-8n1 | 885 | 5d0e00bcda01ee9011581bd444606da5211b5eaebe9d600d61ba227ab4c9581e | a0675441cdc92c3a199135a378c07c8cbc55f20ef3e85655c0e83e0875741fe8 |
| e14-puck-grid-h-9600-8n1 | 3209 | 1ed6449449d3dfd82d32ba1f1d9680efc9d2681135be06af751d0b2322e6aa67 | 5543cfc093ec794998d92af2e883a2b5bc98dad902b88f712ad0c2c222cea24b |
| e15-puck-grid-i-9600-8n1 | 1943 | 397362d536f5c457e53e927ecfc2150dc6c72796d9f264d0eaffdf4e12dc140f | 3f87106f67c99a375398c0da3b1a89601c7f00d0aaed558c34e5a81cf00b45a0 |
| e16-puck-grid-f-9600-8n1 | 2610 | df840215a3d7aa8238978a6360595d3bf4678985d99bd31a2dbb17cad18c9afc | c7023c090aafd2c5120be6467d47e8e4964deeeb0149c2b2f8a6f3bca0eb1cf3 |
| e17-puck-grid-e-9600-8n1 | 2340 | 304e0af6d9e9b9ec7a18b0a5f6f2c3d1088eafa460145d84b6c53aa058db3774 | 6831b17074d00242f54242ed78126128ec22ddb35bd04e2405fa6a6ce9cd3b57 |
| e18-puck-grid-d-9600-8n1 | 2390 | 64533cfbcb58a93adfa64b8ea1691d8693164f5b8a3ddbe1a9c131d762d586a1 | fc8e1d9ee309780499f1b1a518ae67995a09896135278effa764d2b29bfc3fad |
| e19-puck-grid-a-9600-8n1 | 2301 | 4e0cc14a5c3fd6a7c8044ecd88bc9dade00fd7713aeff8ef8ebaac41b24a8102 | 541b3c084a87795f6edf04c405ca1448d4fb0d9c4a11607e5f99495c9f610d46 |
| e20-puck-grid-b-9600-8n1 | 3085 | ca726759812c9cd91772e51e2edbbfe1655f22f6884fab2c04bd1b3126ab4bb8 | ffbc374c7fbb46f9b18fc683ce17b86c4049e9b9c740a388406e7997efc9d916 |
| e21-puck-grid-c-9600-8n1 | 2850 | 8ec186d976cc21761190f1b44c766e4b37cd94ec07da1292fdbfa51d0f7858d4 | 14a6926f50d8bba2ccdf8c85f30f9034500ffa4aa9109877ee0d12e5921a033a |
| e22-puck-grid-e-return-9600-8n1 | 2670 | 6a551c93505d249ff2a855889e1fc61cc5eb1c6c460f8a06247d460256b6f1f0 | 7258f992007d8981f969ef9d26cc8e5362af46266d337cf9cd381c16642ea721 |
| e23-pen-center-behavior-9600-8n1 | 6745 | bce7e9d32495d16f6c673d2fa5c0c358dd8efb468f5137f50e46be0ae55bcc9c | 19991b7896485c2002ef7ce8554d4b6a3e7d62583df26cb28d1dbdeb1e59243c |
| e24-pen-hover-only-9600-8n1 | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | 397224770580b3de1d10968d4bac69bc914a2e0ae88198938c779e9caac09e73 |
| e25-pen-tip-only-9600-8n1 | 2485 | e07494e4bfa28fec84e982b67047fe2c981d85e7c85efd275b622efe950fd903 | 3b2e86598b61f5538842bedb6144517c34acf569c9c48ae2673bac676a2b61a3 |
| e26-pen-side-only-9600-8n1 | 3120 | 009f703739539182e8452ccd9c90c3e7850856715009836652c8291ee9e03dea | 2d19c177c09431d717ecc467fcfc3aa997daa4f38f2aff7d9da89e5a2ae3bd07 |
| e27-pen-grid-g-9600-8n1 | 2085 | 3c798f2667f8e47dba365826e72b49f9fc919dc9da4832c554192aeb86a2ec0a | 2579e3199fe937dd4a5013ccfac200cd86ec8786b889838c0e993bfc1addda9a |
| e28-pen-grid-g-repeat-9600-8n1 | 1180 | 0320d7f5debdb525827d1a4e7819bc5ae289863d65a87628fd9f59a76fb739f0 | 368d9c1d866a25e52f81a25a92b6794901c5a62125df860279cf2269c5c5db49 |

## Tool validation and research boundary

28 synthetic unit tests passed before these trials; PTYs validate tooling, not
tablet success. Acquisition receipts and the attributed MM reference remain
under [source provenance](../research/sources.md). The researcher has seen MM
manual BASIC examples; the [clean-room boundary](../research/clean-room.md)
requires a fresh implementation context. No production decoder was implemented.

## Session close

The operator ended testing after pen G. Remaining pen targets are deferred;
there is no need to finish this approximate grid before offline specification
work. The last capture closed; later tablet power state is unknown. Further
hardware testing requires a new explicit operator-guided session. See the
[prioritized plan](../integration/roadmap.md#next-session).
