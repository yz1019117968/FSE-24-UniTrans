cd ..
CUDA_VISIBLE_DEVICES=0,1,2,3 python codegen.py --checkpoint Salesforce/codegen-16B-multi \
	--src_lang cpp --dst_lang python --k 10 --start 1
