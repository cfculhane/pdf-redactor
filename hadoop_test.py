ticket_cache_path="/tmp/krb5cc_60661" # this you can get with "klist -l" in the shell, after running kinit
host = "hdfs://CHROCHE01CDH"
port = 0
user = "hibellm"

import pyarrow as pa
fs = pa.hdfs.connect(host, port, user=user, kerb_ticket=ticket_cache_path)

path = 'home/users/hibellm/'
print(fs.HadoopFileSystem.ls(path))

# h = fs.open("/user/hibellm/myname.txt", 'rb')
# content = h.read()
# h.close()