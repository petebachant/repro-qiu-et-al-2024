mdls="WRHigh"
wsize=0.06
ssize=0.14
iy=1
ids="1"
ccs="0"
for cc in $ccs;do
for mdl in $mdls;do
for id in `seq 1 1`;do
	python step1_resources.py ${mdl} 0 0 $wsize $ssize 0 $cc $iy $id
	python step2_cost.py ${mdl} 0 0 $wsize $ssize 0 $cc $iy $id
done
done
done



