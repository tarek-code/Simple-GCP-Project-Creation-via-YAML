#!/bin/bash

# Fix all unsafe session state accesses
# Replace direct attribute access with .get() method

cd /media/mario/NewVolume/Simple-GCP-Project-Creation-via-YAML

# Backup the file first
cp gui/streamlit_app.py gui/streamlit_app.py.backup

# Fix all the unsafe session state checks
sed -i 's/if st\.session_state\.vpcs:/if st.session_state.get("vpcs"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.subnets:/if st.session_state.get("subnets"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.firewall_rules:/if st.session_state.get("firewall_rules"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.service_accounts:/if st.session_state.get("service_accounts"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.compute_instances:/if st.session_state.get("compute_instances"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.storage_buckets:/if st.session_state.get("storage_buckets"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.pubsub_topics:/if st.session_state.get("pubsub_topics"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.cloud_run_services:/if st.session_state.get("cloud_run_services"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.cloud_sql_instances:/if st.session_state.get("cloud_sql_instances"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.artifact_repos:/if st.session_state.get("artifact_repos"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.secrets:/if st.session_state.get("secrets"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.dns_zones:/if st.session_state.get("dns_zones"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.bigquery_datasets:/if st.session_state.get("bigquery_datasets"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.cloud_functions:/if st.session_state.get("cloud_functions"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.gke_clusters:/if st.session_state.get("gke_clusters"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.cloud_routers:/if st.session_state.get("cloud_routers"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.cloud_nats:/if st.session_state.get("cloud_nats"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.static_ips:/if st.session_state.get("static_ips"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.disks:/if st.session_state.get("disks"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.redis_instances:/if st.session_state.get("redis_instances"):/' gui/streamlit_app.py
sed -i 's/if st\.session_state\.serverless_vpc_connectors:/if st.session_state.get("serverless_vpc_connectors"):/' gui/streamlit_app.py

echo "✅ Session state accesses fixed"

# Validate syntax
python3 -m py_compile gui/streamlit_app.py
if [ $? -eq 0 ]; then
    echo "✅ Syntax validation passed"
    rm gui/streamlit_app.py.backup
else
    echo "❌ Syntax error found. Restoring backup..."
    mv gui/streamlit_app.py.backup gui/streamlit_app.py
fi
