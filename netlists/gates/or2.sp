* Standard Static CMOS OR2 (16nm LP)
.include "models/16nm_LP.pm"
.param p_vdd=1.0 p_temp=27.0 p_wn=32n p_wp=64n p_l=16n p_ldiff=40n
.param p_ad_n='p_wn*p_ldiff' p_pd_n='2*(p_wn+p_ldiff)'
.param p_ad_p='p_wp*p_ldiff' p_pd_p='2*(p_wp+p_ldiff)'

Vdd vdd 0 DC p_vdd
Va  a   0 DC 0.0
Vb  b   0 DC 0.0

* NOR2 Stage
Mp1 y       a vdd vdd pmos W=p_wp L=p_l AD=p_ad_p AS=p_ad_p PD=p_pd_p PS=p_pd_p
Mp2 nor_out b y   vdd pmos W=p_wp L=p_l AD=p_ad_p AS=p_ad_p PD=p_pd_p PS=p_pd_p
Mn1 nor_out a 0   0   nmos W=p_wn L=p_l AD=p_ad_n AS=p_ad_n PD=p_pd_n PS=p_pd_n
Mn2 nor_out b 0   0   nmos W=p_wn L=p_l AD=p_ad_n AS=p_ad_n PD=p_pd_n PS=p_pd_n

* Inverter Stage
Mpi out nor_out vdd vdd pmos W=p_wp L=p_l AD=p_ad_p AS=p_ad_p PD=p_pd_p PS=p_pd_p
Mni out nor_out 0   0   nmos W=p_wn L=p_l AD=p_ad_n AS=p_ad_n PD=p_pd_n PS=p_pd_n

.options gmin=1e-18 abstol=1e-18 reltol=1e-6 vntol=1e-9
.temp {p_temp}
.op
.end
