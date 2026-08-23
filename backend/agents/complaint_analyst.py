import json
import numpy as np
from sqlalchemy.orm import Session
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from backend.database.models import Complaint, ComplaintCluster
from backend.llm import llm

embedding_model = FastEmbedEmbeddings()

class ComplaintAnalyst:
    
    def cluster_complaints(self, db: Session) -> list:
        """
        Scans all 'Pending' student complaints in the database, generates semantic embeddings
        using FastEmbed, groups them using cosine similarity (>0.75), and compiles
        systemic issue alerts and AI action briefs for administrators.
        """
        # 1. Fetch pending complaints
        pending = db.query(Complaint).filter(Complaint.status == "Pending").all()
        if len(pending) < 2:
            return []

        # 2. Generate embeddings
        descriptions = [c.description for c in pending]
        try:
            embeddings = embedding_model.embed_documents(descriptions)
        except Exception as e:
            print(f"Failed to generate embeddings: {e}")
            return []
            
        vectors = np.array(embeddings)
        num_complaints = len(pending)
        visited = set()
        clusters = []

        # 3. Cluster similar complaints based on cosine similarity
        for i in range(num_complaints):
            if i in visited:
                continue
            
            current_group = [i]
            visited.add(i)
            
            for j in range(num_complaints):
                if j in visited:
                    continue
                
                # BGE ONNX embeddings are L2 normalized, so dot product equals cosine similarity
                sim = float(np.dot(vectors[i], vectors[j]))
                if sim >= 0.75:
                    current_group.append(j)
                    visited.add(j)
            
            if len(current_group) > 1:
                clusters.append([pending[idx] for idx in current_group])

        created_clusters = []
        
        # 4. Generate AI Action Briefs for each cluster
        for group in clusters:
            complaints_text = "\n".join([f"- Dept: {c.department} | Text: {c.description}" for c in group])
            
            prompt = f"""
You are the Campus AI Operations Analyst.

You have detected a cluster of semantically similar student complaints describing a common systemic issue:

Complaints:
{complaints_text}

Provide:
1. A concise, professional title summarizing the systemic issue (max 6 words).
2. An AI Action Brief for the administrator explaining the underlying issue, affected departments/locations, and urgency.

Return ONLY a valid JSON object matching the following structure (do NOT write markdown syntax, codeblocks, or other text):
{{
    "title": "...",
    "brief": "..."
}}
"""
            try:
                response = llm.invoke(prompt)
                text = response.content.strip()
                
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                text = text.strip()
                
                ai_data = json.loads(text)
            except Exception as e:
                print(f"LLM compilation of action brief failed: {e}")
                ai_data = {
                    "title": f"Systemic Issue in {group[0].department} Department",
                    "brief": f"Multiple students reported issues regarding: {group[0].description}"
                }
            
            # Save cluster to database
            cluster = ComplaintCluster(
                ai_title=ai_data.get("title", f"Systemic Issue in {group[0].department}"),
                ai_brief=ai_data.get("brief", "Multiple complaints grouped by semantic similarity."),
                status="Active"
            )
            db.add(cluster)
            db.commit()
            db.refresh(cluster)
            
            # Assign complaints to the cluster and update status
            for complaint in group:
                complaint.cluster_id = cluster.id
                complaint.status = "Clustered"
            db.commit()
            
            created_clusters.append(cluster)
            
        return created_clusters
