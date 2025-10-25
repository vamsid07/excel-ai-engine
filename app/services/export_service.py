"""
Export Service for saving query results
"""
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import io


class ExportService:
    """Service for exporting DataFrames to Excel"""
    
    def __init__(self):
        self.output_dir = Path("data/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_excel(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        sheet_name: str = 'Result',
        include_index: bool = False
    ) -> str:
        """
        Export DataFrame to Excel file
        
        Args:
            df: DataFrame to export
            filename: Output filename (auto-generated if None)
            sheet_name: Name of the sheet
            include_index: Whether to include index
            
        Returns:
            Output file path
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"query_result_{timestamp}.xlsx"
        
        # Ensure .xlsx extension
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        filepath = self.output_dir / filename
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=include_index)
            
            return str(filepath)
            
        except Exception as e:
            raise ValueError(f"Export failed: {str(e)}")
    
    def export_multiple_sheets(
        self,
        dataframes: Dict[str, pd.DataFrame],
        filename: str,
        include_index: bool = False
    ) -> str:
        """
        Export multiple DataFrames as different sheets
        
        Args:
            dataframes: Dict mapping sheet names to DataFrames
            filename: Output filename
            include_index: Whether to include index
            
        Returns:
            Output file path
        """
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        filepath = self.output_dir / filename
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                for sheet_name, df in dataframes.items():
                    # Sanitize sheet name (max 31 chars, no special chars)
                    clean_sheet_name = self._sanitize_sheet_name(sheet_name)
                    df.to_excel(writer, sheet_name=clean_sheet_name, index=include_index)
            
            return str(filepath)
            
        except Exception as e:
            raise ValueError(f"Multi-sheet export failed: {str(e)}")
    
    def export_with_formatting(
        self,
        df: pd.DataFrame,
        filename: str,
        sheet_name: str = 'Result',
        format_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export DataFrame with custom formatting
        
        Args:
            df: DataFrame to export
            filename: Output filename
            sheet_name: Sheet name
            format_config: Formatting configuration
            
        Returns:
            Output file path
        """
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        filepath = self.output_dir / filename
        
        try:
            from openpyxl.styles import Font, PatternFill
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Get the worksheet
                worksheet = writer.sheets[sheet_name]
                
                # Apply header formatting
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(cell.value)
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            return str(filepath)
            
        except Exception as e:
            raise ValueError(f"Formatted export failed: {str(e)}")
    
    def export_to_csv(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        include_index: bool = False
    ) -> str:
        """
        Export DataFrame to CSV file
        
        Args:
            df: DataFrame to export
            filename: Output filename
            include_index: Whether to include index
            
        Returns:
            Output file path
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"query_result_{timestamp}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        filepath = self.output_dir / filename
        
        try:
            df.to_csv(filepath, index=include_index)
            return str(filepath)
        except Exception as e:
            raise ValueError(f"CSV export failed: {str(e)}")
    
    def get_export_summary(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Get summary of data being exported
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Summary statistics
        """
        return {
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'null_counts': df.isnull().sum().to_dict(),
            'dtypes': df.dtypes.astype(str).to_dict()
        }
    
    def _sanitize_sheet_name(self, name: str) -> str:
        """
        Sanitize sheet name for Excel compatibility
        
        Args:
            name: Original sheet name
            
        Returns:
            Sanitized sheet name
        """
        # Remove invalid characters
        invalid_chars = ['[', ']', '*', '?', ':', '/', '\\']
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Limit to 31 characters (Excel limit)
        return name[:31]
    
    def list_exports(self) -> list:
        """
        List all exported files
        
        Returns:
            List of export file info
        """
        exports = []
        
        for filepath in self.output_dir.glob('*.xlsx'):
            exports.append({
                'filename': filepath.name,
                'filepath': str(filepath),
                'size_mb': filepath.stat().st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(filepath.stat().st_ctime).isoformat()
            })
        
        return sorted(exports, key=lambda x: x['created'], reverse=True)