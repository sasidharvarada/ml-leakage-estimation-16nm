* 3-bit CLA, vector 1010101 (cin b2 b1 b0 a2 a1 a0 = bit6..bit0)
.model  nmos_mod  nmos  level = 54


+version = 4.0             binunit = 1               paramchk= 1               mobmod  = 0             
+capmod  = 2               igcmod  = 1               igbmod  = 1               geomod  = 1             
+diomod  = 1               rdsmod  = 0               rbodymod= 1               rgatemod= 1             
+permod  = 1               acnqsmod= 0               trnqsmod= 0             

+tnom    = 27              toxe    = 1.200000e-09        toxp    = 9e-010          toxm    = 1.2e-009      
+dtox    = 3e-010          epsrox  = 3.9             wint    = 5e-009          lint    = 0             
+ll      = 0               wl      = 0               lln     = 1               wln     = 1             
+lw      = 0               ww      = 0               lwn     = 1               wwn     = 1             
+lwl     = 0               wwl     = 0               xpart   = 0               toxref  = 1.2e-009      

+vth0    = 6.819100e-01         k1      = 0.4             k2      = 0               k3      = 0             
+k3b     = 0               w0      = 2.5e-006        dvt0    = 1               dvt1    = 2             
+dvt2    = 0               dvt0w   = 0               dvt1w   = 0               dvt2w   = 0             
+dsub    = 0.1             minv    = 0.05            voffl   = 0               dvtp0   = 1e-011        
+dvtp1   = 0.1             lpe0    = 0               lpeb    = 0               xj      = 5.000000e-09        
+ngate   = 1e+023          ndep    = 7.000000e+18          nsd     = 2e+020          phin    = 0             
+cdsc    = 0               cdscb   = 0               cdscd   = 0               cit     = 0             
+voff    = -0.1014         nfactor = 1.6             eta0    = 0.0095          etab    = 0             
+vfb     = -0.55           u0      = 2.800000e-02           ua      = 6e-010          ub      = 1.2e-018      
+uc      = 0               vsat    = 200000          a0      = 1               ags     = 0             
+a1      = 0               a2      = 1               b0      = 0               b1      = 0             
+keta    = 0.04            dwg     = 0               dwb     = 0               pclm    = 0.02          
+pdiblc1 = 0.001           pdiblc2 = 0.001           pdiblcb = -0.005          drout   = 0.5           
+pvag    = 1e-020          delta   = 0.01            pscbe1  = 8.14e+008       pscbe2  = 1e-007        
+fprout  = 0.2             pdits   = 0.01            pditsd  = 0.23            pditsl  = 2300000       
+rsh     = 5               rdsw    = 170             rsw     = 75              rdw     = 75            
+rdswmin = 0               rdwmin  = 0               rswmin  = 0               prwg    = 0             
+prwb    = 0               wr      = 1               alpha0  = 0.074           alpha1  = 0.005         
+beta0   = 30              agidl   = 0.0002          bgidl   = 2.1e+009        cgidl   = 0.0002        
+egidl   = 0.8             aigbacc = 0.012           bigbacc = 0.0028          cigbacc = 0.002         
+nigbacc = 1               aigbinv = 0.014           bigbinv = 0.004           cigbinv = 0.004         
+eigbinv = 1.1             nigbinv = 3               aigc    = 0.015211        bigc    = 0.0027432     
+cigc    = 0.002           aigsd   = 0.015211        bigsd   = 0.0027432       cigsd   = 0.002         
+nigc    = 1               poxedge = 1               pigcd   = 1               ntox    = 1             
+xrcrg1  = 12              xrcrg2  = 5             

+cgso    = 5e-011          cgdo    = 5e-011          cgbo    = 2.56e-011       cgdl    = 2.653e-010    
+cgsl    = 2.653e-010      ckappas = 0.03            ckappad = 0.03            acde    = 1             
+moin    = 15              noff    = 0.9             voffcv  = 0.02          

+kt1     = -0.11           kt1l    = 0               kt2     = 0.022           ute     = -1.5          
+ua1     = 4.31e-009       ub1     = 7.61e-018       uc1     = -5.6e-011       prt     = 0             
+at      = 33000         

+fnoimod = 1               tnoimod = 0             

+jss     = 0.0001          jsws    = 1e-011          jswgs   = 1e-010          njs     = 1             
+ijthsfwd= 0.01            ijthsrev= 0.001           bvs     = 10              xjbvs   = 1             
+jsd     = 0.0001          jswd    = 1e-011          jswgd   = 1e-010          njd     = 1             
+ijthdfwd= 0.01            ijthdrev= 0.001           bvd     = 10              xjbvd   = 1             
+pbs     = 1               cjs     = 0.0005          mjs     = 0.5             pbsws   = 1             
+cjsws   = 5e-010          mjsws   = 0.33            pbswgs  = 1               cjswgs  = 3e-010        
+mjswgs  = 0.33            pbd     = 1               cjd     = 0.0005          mjd     = 0.5           
+pbswd   = 1               cjswd   = 5e-010          mjswd   = 0.33            pbswgd  = 1             
+cjswgd  = 5e-010          mjswgd  = 0.33            tpb     = 0.005           tcj     = 0.001         
+tpbsw   = 0.005           tcjsw   = 0.001           tpbswg  = 0.005           tcjswg  = 0.001         
+xtis    = 3               xtid    = 3             

+dmcg    = 0               dmci    = 0               dmdg    = 0               dmcgt   = 0             
+dwj     = 0               xgw     = 0               xgl     = 0             

+rshg    = 0.4             gbmin   = 1e-010          rbpb    = 5               rbpd    = 15            
+rbps    = 15              rbdb    = 15              rbsb    = 15              ngcon   = 1
.model  pmos_mod  pmos  level = 54


+version = 4.0             binunit = 1               paramchk= 1               mobmod  = 0             
+capmod  = 2               igcmod  = 1               igbmod  = 1               geomod  = 1             
+diomod  = 1               rdsmod  = 0               rbodymod= 1               rgatemod= 1             
+permod  = 1               acnqsmod= 0               trnqsmod= 0             

+tnom    = 27              toxe    = 1.220000e-09       toxp    = 9e-010          toxm    = 1.22e-009     
+dtox    = 3.2e-010        epsrox  = 3.9             wint    = 5e-009          lint    = 8e-010        
+ll      = 0               wl      = 0               lln     = 1               wln     = 1             
+lw      = 0               ww      = 0               lwn     = 1               wwn     = 1             
+lwl     = 0               wwl     = 0               xpart   = 0               toxref  = 1.22e-009     

+vth0    = -6.862000e-01         k1      = 0.4             k2      = -0.01           k3      = 0             
+k3b     = 0               w0      = 2.5e-006        dvt0    = 1               dvt1    = 2             
+dvt2    = -0.032          dvt0w   = 0               dvt1w   = 0               dvt2w   = 0             
+dsub    = 0.1             minv    = 0.05            voffl   = 0               dvtp0   = 1e-011        
+dvtp1   = 0.05            lpe0    = 0               lpeb    = 0               xj      = 7.200000e-09      
+ngate   = 1e+023          ndep    = 4.400000e+18        nsd     = 2e+020          phin    = 0             
+cdsc    = 0               cdscb   = 0               cdscd   = 0               cit     = 0             
+voff    = -0.08           nfactor = 1.8             eta0    = 0.0095          etab    = 0             
+vfb     = 0.55            u0      = 7.500000e-03          ua      = 2e-009          ub      = 5e-019        
+uc      = 0               vsat    = 195000          a0      = 1               ags     = 1e-020        
+a1      = 0               a2      = 1               b0      = 0               b1      = 0             
+keta    = -0.047          dwg     = 0               dwb     = 0               pclm    = 0.12          
+pdiblc1 = 0.001           pdiblc2 = 0.001           pdiblcb = 3.4e-008        drout   = 0.56          
+pvag    = 1e-020          delta   = 0.01            pscbe1  = 8.14e+008       pscbe2  = 9.58e-007     
+fprout  = 0.2             pdits   = 0.08            pditsd  = 0.23            pditsl  = 2300000       
+rsh     = 5               rdsw    = 220             rsw     = 72.5            rdw     = 72.5          
+rdswmin = 0               rdwmin  = 0               rswmin  = 0               prwg    = 0             
+prwb    = 0               wr      = 1               alpha0  = 0.074           alpha1  = 0.005         
+beta0   = 30              agidl   = 0.0002          bgidl   = 2.1e+009        cgidl   = 0.0002        
+egidl   = 0.8             aigbacc = 0.012           bigbacc = 0.0028          cigbacc = 0.002         
+nigbacc = 1               aigbinv = 0.014           bigbinv = 0.004           cigbinv = 0.004         
+eigbinv = 1.1             nigbinv = 3               aigc    = 0.0097          bigc    = 0.00125       
+cigc    = 0.0008          aigsd   = 0.0115           bigsd   = 0.00125         cigsd   = 0.0008        
+nigc    = 1               poxedge = 1               pigcd   = 1               ntox    = 1             
+xrcrg1  = 12              xrcrg2  = 5             

+cgso    = 5e-011          cgdo    = 5e-011          cgbo    = 2.56e-011       cgdl    = 2.653e-010    
+cgsl    = 2.653e-010      ckappas = 0.03            ckappad = 0.03            acde    = 1             
+moin    = 15              noff    = 0.9             voffcv  = 0.02          

+kt1     = -0.11           kt1l    = 0               kt2     = 0.022           ute     = -1.5          
+ua1     = 4.31e-009       ub1     = 7.61e-018       uc1     = -5.6e-011       prt     = 0             
+at      = 33000         

+fnoimod = 1               tnoimod = 0             

+jss     = 0.0001          jsws    = 1e-011          jswgs   = 1e-010          njs     = 1             
+ijthsfwd= 0.01            ijthsrev= 0.001           bvs     = 10              xjbvs   = 1             
+jsd     = 0.0001          jswd    = 1e-011          jswgd   = 1e-010          njd     = 1             
+ijthdfwd= 0.01            ijthdrev= 0.001           bvd     = 10              xjbvd   = 1             
+pbs     = 1               cjs     = 0.0005          mjs     = 0.5             pbsws   = 1             
+cjsws   = 5e-010          mjsws   = 0.33            pbswgs  = 1               cjswgs  = 3e-010        
+mjswgs  = 0.33            pbd     = 1               cjd     = 0.0005          mjd     = 0.5           
+pbswd   = 1               cjswd   = 5e-010          mjswd   = 0.33            pbswgd  = 1             
+cjswgd  = 5e-010          mjswgd  = 0.33            tpb     = 0.005           tcj     = 0.001         
+tpbsw   = 0.005           tcjsw   = 0.001           tpbswg  = 0.005           tcjswg  = 0.001         
+xtis    = 3               xtid    = 3             

+dmcg    = 0               dmci    = 0               dmdg    = 0               dmcgt   = 0             
+dwj     = 0               xgw     = 0               xgl     = 0             

+rshg    = 0.4             gbmin   = 1e-010          rbpb    = 5               rbpd    = 15            
+rbps    = 15              rbdb    = 15              rbsb    = 15              ngcon   = 1
Vdd vdd 0 DC 1.000000
Va0 a0 0 DC 1.000000
Va1 a1 0 DC 0.000000
Va2 a2 0 DC 1.000000
Vb0 b0 0 DC 0.000000
Vb1 b1 0 DC 1.000000
Vb2 b2 0 DC 0.000000
Vcin cin 0 DC 1.000000
Mg0p1 p0_n1 a0 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg0p2 p0_n1 b0 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg0n1 p0_n1 a0 g0_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg0n2 g0_x b0 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg1p1 p0_n2 a0 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg1p2 p0_n2 p0_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg1n1 p0_n2 a0 g1_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg1n2 g1_x p0_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg2p1 p0_n3 b0 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg2p2 p0_n3 p0_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg2n1 p0_n3 b0 g2_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg2n2 g2_x p0_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg3p1 p0 p0_n2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg3p2 p0 p0_n3 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg3n1 p0 p0_n2 g3_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg3n2 g3_x p0_n3 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg4p1 g4_n a0 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg4p2 g4_n b0 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg4n1 g4_n a0 g4_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg4n2 g4_x b0 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg4ip g0n g4_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg4in g0n g4_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg5p1 p1_n1 a1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg5p2 p1_n1 b1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg5n1 p1_n1 a1 g5_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg5n2 g5_x b1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg6p1 p1_n2 a1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg6p2 p1_n2 p1_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg6n1 p1_n2 a1 g6_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg6n2 g6_x p1_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg7p1 p1_n3 b1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg7p2 p1_n3 p1_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg7n1 p1_n3 b1 g7_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg7n2 g7_x p1_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg8p1 p1 p1_n2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg8p2 p1 p1_n3 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg8n1 p1 p1_n2 g8_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg8n2 g8_x p1_n3 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg9p1 g9_n a1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg9p2 g9_n b1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg9n1 g9_n a1 g9_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg9n2 g9_x b1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg9ip g1n g9_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg9in g1n g9_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg10p1 p2_n1 a2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg10p2 p2_n1 b2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg10n1 p2_n1 a2 g10_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg10n2 g10_x b2 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg11p1 p2_n2 a2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg11p2 p2_n2 p2_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg11n1 p2_n2 a2 g11_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg11n2 g11_x p2_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg12p1 p2_n3 b2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg12p2 p2_n3 p2_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg12n1 p2_n3 b2 g12_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg12n2 g12_x p2_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg13p1 p2 p2_n2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg13p2 p2 p2_n3 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg13n1 p2 p2_n2 g13_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg13n2 g13_x p2_n3 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg14p1 g14_n a2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg14p2 g14_n b2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg14n1 g14_n a2 g14_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg14n2 g14_x b2 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg14ip g2n g14_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg14in g2n g14_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg15p1 g15_n p0 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg15p2 g15_n cin vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg15n1 g15_n p0 g15_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg15n2 g15_x cin 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg15ip t1 g15_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg15in t1 g15_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg16p1 g16_y g0n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg16p2 g16_n t1 g16_y vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg16n1 g16_n g0n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg16n2 g16_n t1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg16ip c1 g16_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg16in c1 g16_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg17p1 g17_n p1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg17p2 g17_n g0n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg17n1 g17_n p1 g17_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg17n2 g17_x g0n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg17ip t2a g17_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg17in t2a g17_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg18p1 g18_n p1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg18p2 g18_n p0 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg18n1 g18_n p1 g18_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg18n2 g18_x p0 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg18ip pp10 g18_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg18in pp10 g18_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg19p1 g19_n pp10 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg19p2 g19_n cin vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg19n1 g19_n pp10 g19_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg19n2 g19_x cin 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg19ip t2c g19_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg19in t2c g19_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg20p1 g20_y g1n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg20p2 g20_n t2a g20_y vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg20n1 g20_n g1n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg20n2 g20_n t2a 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg20ip u g20_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg20in u g20_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg21p1 g21_y u vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg21p2 g21_n t2c g21_y vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg21n1 g21_n u 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg21n2 g21_n t2c 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg21ip c2 g21_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg21in c2 g21_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg22p1 g22_n p2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg22p2 g22_n g1n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg22n1 g22_n p2 g22_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg22n2 g22_x g1n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg22ip t3a g22_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg22in t3a g22_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg23p1 g23_n p2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg23p2 g23_n p1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg23n1 g23_n p2 g23_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg23n2 g23_x p1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg23ip pp21 g23_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg23in pp21 g23_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg24p1 g24_n pp21 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg24p2 g24_n g0n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg24n1 g24_n pp21 g24_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg24n2 g24_x g0n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg24ip t3b g24_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg24in t3b g24_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg25p1 g25_n p2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg25p2 g25_n pp10 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg25n1 g25_n p2 g25_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg25n2 g25_x pp10 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg25ip pp210 g25_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg25in pp210 g25_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg26p1 g26_n pp210 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg26p2 g26_n cin vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg26n1 g26_n pp210 g26_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg26n2 g26_x cin 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg26ip t3c g26_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg26in t3c g26_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg27p1 g27_y g2n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg27p2 g27_n t3a g27_y vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg27n1 g27_n g2n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg27n2 g27_n t3a 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg27ip v1 g27_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg27in v1 g27_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg28p1 g28_y v1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg28p2 g28_n t3b g28_y vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg28n1 g28_n v1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg28n2 g28_n t3b 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg28ip v2 g28_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg28in v2 g28_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg29p1 g29_y v2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg29p2 g29_n t3c g29_y vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg29n1 g29_n v2 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg29n2 g29_n t3c 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg29ip cout g29_n vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg29in cout g29_n 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg30p1 s0_n1 p0 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg30p2 s0_n1 cin vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg30n1 s0_n1 p0 g30_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg30n2 g30_x cin 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg31p1 s0_n2 p0 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg31p2 s0_n2 s0_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg31n1 s0_n2 p0 g31_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg31n2 g31_x s0_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg32p1 s0_n3 cin vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg32p2 s0_n3 s0_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg32n1 s0_n3 cin g32_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg32n2 g32_x s0_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg33p1 s0 s0_n2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg33p2 s0 s0_n3 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg33n1 s0 s0_n2 g33_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg33n2 g33_x s0_n3 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg34p1 s1_n1 p1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg34p2 s1_n1 c1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg34n1 s1_n1 p1 g34_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg34n2 g34_x c1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg35p1 s1_n2 p1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg35p2 s1_n2 s1_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg35n1 s1_n2 p1 g35_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg35n2 g35_x s1_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg36p1 s1_n3 c1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg36p2 s1_n3 s1_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg36n1 s1_n3 c1 g36_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg36n2 g36_x s1_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg37p1 s1 s1_n2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg37p2 s1 s1_n3 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg37n1 s1 s1_n2 g37_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg37n2 g37_x s1_n3 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg38p1 s2_n1 p2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg38p2 s2_n1 c2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg38n1 s2_n1 p2 g38_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg38n2 g38_x c2 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg39p1 s2_n2 p2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg39p2 s2_n2 s2_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg39n1 s2_n2 p2 g39_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg39n2 g39_x s2_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg40p1 s2_n3 c2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg40p2 s2_n3 s2_n1 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg40n1 s2_n3 c2 g40_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg40n2 g40_x s2_n1 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg41p1 s2 s2_n2 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg41p2 s2 s2_n3 vdd vdd pmos_mod W=6.40000e-08 L=1.60000e-08 AD=2.56000e-15 AS=2.56000e-15 PD=2.08000e-07 PS=2.08000e-07
Mg41n1 s2 s2_n2 g41_x 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
Mg41n2 g41_x s2_n3 0 0 nmos_mod W=3.20000e-08 L=1.60000e-08 AD=1.28000e-15 AS=1.28000e-15 PD=1.44000e-07 PS=1.44000e-07
.nodeset v(g0_x)=1.0000 v(p0_n1)=1.0000 v(g1_x)=0.0000 v(p0_n2)=0.0000 v(g2_x)=0.0000 v(p0_n3)=1.0000 v(g3_x)=0.0000 v(p0)=1.0000 v(g4_x)=1.0000 v(g4_n)=1.0000 v(g0n)=0.0000 v(g5_x)=0.0000 v(p1_n1)=1.0000 v(g6_x)=0.0000 v(p1_n2)=1.0000 v(g7_x)=0.0000 v(p1_n3)=0.0000 v(g8_x)=1.0000 v(p1)=1.0000 v(g9_x)=0.0000 v(g9_n)=1.0000 v(g1n)=0.0000 v(g10_x)=1.0000 v(p2_n1)=1.0000 v(g11_x)=0.0000 v(p2_n2)=0.0000 v(g12_x)=0.0000 v(p2_n3)=1.0000 v(g13_x)=0.0000 v(p2)=1.0000 v(g14_x)=1.0000 v(g14_n)=1.0000 v(g2n)=0.0000 v(g15_x)=0.0000 v(g15_n)=0.0000 v(t1)=1.0000 v(g16_y)=1.0000 v(g16_n)=0.0000 v(c1)=1.0000 v(g17_x)=1.0000 v(g17_n)=1.0000 v(t2a)=0.0000 v(g18_x)=0.0000 v(g18_n)=0.0000 v(pp10)=1.0000 v(g19_x)=0.0000 v(g19_n)=0.0000 v(t2c)=1.0000 v(g20_y)=1.0000 v(g20_n)=1.0000 v(u)=0.0000 v(g21_y)=1.0000 v(g21_n)=0.0000 v(c2)=1.0000 v(g22_x)=1.0000 v(g22_n)=1.0000 v(t3a)=0.0000 v(g23_x)=0.0000 v(g23_n)=0.0000 v(pp21)=1.0000 v(g24_x)=1.0000 v(g24_n)=1.0000 v(t3b)=0.0000 v(g25_x)=0.0000 v(g25_n)=0.0000 v(pp210)=1.0000 v(g26_x)=0.0000 v(g26_n)=0.0000 v(t3c)=1.0000 v(g27_y)=1.0000 v(g27_n)=1.0000 v(v1)=0.0000 v(g28_y)=1.0000 v(g28_n)=1.0000 v(v2)=0.0000 v(g29_y)=1.0000 v(g29_n)=0.0000 v(cout)=1.0000 v(g30_x)=0.0000 v(s0_n1)=0.0000 v(g31_x)=1.0000 v(s0_n2)=1.0000 v(g32_x)=1.0000 v(s0_n3)=1.0000 v(g33_x)=0.0000 v(s0)=0.0000 v(g34_x)=0.0000 v(s1_n1)=0.0000 v(g35_x)=1.0000 v(s1_n2)=1.0000 v(g36_x)=1.0000 v(s1_n3)=1.0000 v(g37_x)=0.0000 v(s1)=0.0000 v(g38_x)=0.0000 v(s2_n1)=0.0000 v(g39_x)=1.0000 v(s2_n2)=1.0000 v(g40_x)=1.0000 v(s2_n3)=1.0000 v(g41_x)=0.0000 v(s2)=0.0000
.options gmin=1e-18 abstol=1e-18 reltol=1e-6 vntol=1e-9 itl1=400
.temp 27.00
.control
set numdgt = 10
op
let ileak = -i(vdd)
echo LEAK $&ileak
echo OUTS $&v(s0) $&v(s1) $&v(s2) $&v(cout)
.endc
.end
