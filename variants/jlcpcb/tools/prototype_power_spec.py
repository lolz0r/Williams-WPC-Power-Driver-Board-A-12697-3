"""JLC-3 power-supply component and connectivity specification.

The pin map is transcribed from TI SLVSH28A, Table 5-1. Native CAD and
independent checks must agree with this specification before export.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
IC_FOOTPRINT = 'wpc_cost:TI_RYQ0021B_5x3mm'
PIN_NAMES = ['EN', 'MODE', 'PG', 'CC', 'DITH', 'FSW', 'VIN', 'SW1',
             'PGND', 'SW2', 'VOUT', 'ISP', 'ISN', 'FB', 'COMP', 'CDC',
             'AGND', 'VCC', 'BOOT2', 'BOOT1', 'EXTVCC']
RAILS = [
    dict(ref='U20', vin='/Power_Supply/+5V_RAW', out='+5V', center=(269., 58.),
         old_caps=['C33','C34','C35','C36','C37','C38'], bulk=['C4','C9'],
         resistors=[f'R{i}' for i in range(261,267)], inductor='L1', diode='D36',
         new_caps=[f'C{i}' for i in range(45,52)], shunt='R326',
         shunt_code='C705606', shunt_ohm=.013, fb_code='C865625', fb_ohm=6650., rc_code='C37252', rc_ohm=33200.,
         cc_code='C49678', cc_f=100e-9, cp_code='C107121', cp_f=680e-12),
    dict(ref='U21', vin='+18V', out='+12V', center=(143., 68.),
         old_caps=['C39','C40','C41','C42','C43','C44'], bulk=['C2','C12'],
         resistors=[f'R{i}' for i in range(267,273)], inductor='L2', diode='D37',
         new_caps=[f'C{i}' for i in range(52,59)], shunt='R327',
         shunt_code='C705608', shunt_ohm=.033, fb_code='C706223', fb_ohm=18000., rc_code='C17686', rc_ohm=42200.,
         cc_code='C73142', cc_f=330e-9, cp_code='C62774', cp_f=1e-9),
]


def catalog_fields(code):
    d = json.loads((ROOT/'research/jlcpcb/catalog'/f'{code}.json').read_text())
    assert d['isBuyComponent'] == '1', code
    return {'MPN': d['componentModelEn'], 'Manufacturer': d['componentBrandEn'],
            'JLCPCB Part': code, 'JLCPCB Library': {'base':'Basic','expand':'Extended'}[d['componentLibraryType']],
            'Link': d['url']}


def components(rail, originals):
    """Return reference -> properties / pin nets; preserve existing bulk parts."""
    r = rail; u = r['ref']; n = lambda suffix: '/Power_Supply/'+u+'_'+suffix
    vin, out, reg = r['vin'], r['out'], n('REG')
    ci1,ci2,cb1,cc,cp,co1 = r['old_caps']
    cb2,cv,chi,cho,ci3,ci4,co2 = r['new_caps']
    en1,en2,rt,fb1,fb2,rc = r['resistors']
    parts = {}
    def part(ref, template, nets, value=None, code=None, fp=None, description=None):
        props = dict(originals[template]); props['Reference'] = ref
        if value is not None: props['Value'] = value
        if code: props.update(catalog_fields(code))
        if fp: props['Footprint'] = fp
        if description: props['Description'] = description
        # Obsolete prices are not estimates for replacement parts.
        props['Price'] = ''; props['Price100'] = ''
        parts[ref] = dict(properties=props, nets={str(k):v for k,v in nets.items()}, template=template)
    icnets = {1:n('EN'),2:'GND',3:None,4:None,5:'GND',6:n('RT'),7:vin,
              8:n('SW1'),9:'GND',10:n('SW2'),11:reg,12:reg,13:out,
              14:n('FB'),15:n('COMP'),16:None,17:'GND',18:n('VCC'),
              19:n('BOOT2'),20:n('BOOT1'),21:None}
    part(u,u,icnets,'TPS552892RYQR','C19272254',IC_FOOTPRINT,
         '36 V synchronous buck-boost; PFM; internal VCC; output current limit; JLC-3')
    def two(ref,template,a,b,**kw): part(ref,template,{1:a,2:b},**kw)
    for ref in [ci1,ci2,ci3,ci4]:
        two(ref,ci1,vin,'GND',description='10 uF 50 V X7R input bypass; four parallel capacitors')
    for ref in [co1,co2]:
        two(ref,co1,reg,'GND',description='10 uF 50 V X7R local output bypass, before current sense')
    for ref in r['bulk']:
        two(ref,ref,out,'GND')
    for ref,a,b in [(cb1,n('BOOT1'),n('SW1')),(cb2,n('BOOT2'),n('SW2')),
                    (chi,vin,'GND'),(cho,reg,'GND')]:
        two(ref,cb1,a,b,value='100nF',code='C77020',fp='Capacitor_SMD:C_0402_1005Metric',
            description='100 nF 50 V X7R; short local bootstrap / high-frequency loop')
    two(cv,ci1,n('VCC'),'GND',description='10 uF 50 V X7R on internal 5.2 V VCC; >4.7 uF effective')
    two(en1,en1,vin,n('EN'),description='TPS552892 UVLO upper resistor; 1.23 V EN reference, 5 uA hysteresis')
    two(en2,en2,n('EN'),'GND',description='TPS552892 UVLO lower resistor')
    two(rt,rt,n('RT'),'GND',value='49.9K',code='C17719',description='395 kHz nominal, TI equation 3')
    two(fb1,fb1,out,n('FB'),value='6.65K' if u=='U20' else '18K',code=r['fb_code'],
        description='Feedback upper resistor; 1.2 V reference; sense after output shunt')
    two(fb2,fb2,n('FB'),'GND',code=None if u=='U20' else 'C865384',description='0.1% feedback lower resistor')
    two(rc,rc,n('COMP'),n('CC'),value='33.2K' if u=='U20' else '42.2K',code=r['rc_code'],description='Outer voltage-loop compensation resistor')
    two(cc,cc,n('CC'),'GND',value='100nF' if u=='U20' else '330nF',code=r['cc_code'],description='TPS552892 compensation series capacitor; TI equation 25')
    two(cp,cp,n('COMP'),'GND',value='680pF' if u=='U20' else '1nF',code=r['cp_code'],description='TPS552892 compensation high-frequency pole capacitor; C0G; TI equation 26')
    two(r['inductor'],r['inductor'],n('SW1'),n('SW2'),description='10 uH buck-boost inductor; 15.5 A saturation rating')
    two(r['shunt'],en1,reg,out,value='13m' if u=='U20' else '33m',code=r['shunt_code'],
        fp='Resistor_SMD:R_2512_6332Metric',description='1 W, 1% output-current shunt; Kelvin ISP/ISN routing')
    return parts
