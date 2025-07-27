import pandas as pd
from datetime import datetime
import os

class ExcelExporter:
    @staticmethod
    def export_project(project_id: str) -> str:
        """
        Exporta un proyecto a Excel
        """
        # Por ahora creamos un archivo de ejemplo
        df = pd.DataFrame({
            'Sample': ['Sample1', 'Sample2'],
            'D3S1358': ['15,17', '16,16'],
            'vWA': ['17,18', '16,19'],
            'FGA': ['22,24', '21,23']
        })
        
        filename = f"export_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(os.path.dirname(__file__), '..', filename)
        
        df.to_excel(filepath, index=False)
        return filepath
    