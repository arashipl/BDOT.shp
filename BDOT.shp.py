import os
import glob
import sys
from osgeo import ogr

def remove_related_files(file_path):
    """Removes files related to a shapefile (e.g., .shx, .dbf, .prj)."""
    base_name = os.path.splitext(file_path)[0]
    extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg']  # Add more extensions if needed
    for ext in extensions:
        related_file = base_name + ext
        if os.path.exists(related_file):
            print(f"Info: Removing related file '{related_file}'.")
            os.remove(related_file)

def deep_copy_field_defn(field_defn_shadow):
    """Creates a deep copy of an OGRFieldDefnShadow object."""
    new_field_defn = ogr.FieldDefn(field_defn_shadow.GetName(), field_defn_shadow.GetType())
    new_field_defn.SetWidth(field_defn_shadow.GetWidth())
    new_field_defn.SetPrecision(field_defn_shadow.GetPrecision())
    new_field_defn.SetJustify(field_defn_shadow.GetJustify())
    new_field_defn.SetSubType(field_defn_shadow.GetSubType())
    new_field_defn.SetNullable(field_defn_shadow.IsNullable())
    new_field_defn.SetUnique(field_defn_shadow.IsUnique())
    new_field_defn.SetDefault(field_defn_shadow.GetDefault())
    return new_field_defn

def merge_shapefiles(input_dir, output_file, pattern, GeomType, exclude_not_needed=False):
    """Merges shapefiles, explicit encoding, and aggressive renaming."""
    matching_files = glob.glob(os.path.join(input_dir, f"*{pattern}.shp"))

    if exclude_not_needed:
        matching_files = [f for f in matching_files if "_KU" not in os.path.basename(f) and "_TCON" not in os.path.basename(f) and "_AD" not in os.path.basename(f) and "_SKDR" not in os.path.basename(f)]
    if not matching_files:
        print(f"Warning: No files found matching pattern '{pattern}' in '{input_dir}'.")
        return

    driver = ogr.GetDriverByName("ESRI Shapefile")

    if os.path.exists(output_file):
        print(f"Info: Removing existing output file '{output_file}'.")
        remove_related_files(output_file) #remove related files

    if os.path.exists(output_file):
        print(f"Info: Overwriting existing output file '{output_file}'.")
        driver.DeleteDataSource(output_file)

    ds_out = driver.CreateDataSource(output_file)
    if ds_out is None:
        print(f"Error: Could not create output shapefile: {output_file}")
        return

    non_empty_file = None
    for file in matching_files:
        ds = driver.Open(file, 0)
        if ds and ds.GetLayer() and ds.GetLayer().GetFeatureCount() > 0:
            non_empty_file = file
            break
        if ds:
            ds = None

    if non_empty_file is None:
        print(f"Error: No non-empty shapefiles found matching pattern '{pattern}'.")
        ds_out = None
        return

    ds_first = driver.Open(non_empty_file, 0)
    if ds_first is None:
        print(f"Error: Could not open shapefile: {non_empty_file}")
        return
    layer_first = ds_first.GetLayer()
    if layer_first is None:
        print(f"Error: Could not get layer from shapefile: {non_empty_file}")
        return
    geom_type = layer_first.GetGeomType()
    srs = layer_first.GetSpatialRef()
    ds_first = None

    layer_out = ds_out.CreateLayer(os.path.splitext(os.path.basename(output_file))[0], srs, geom_type, options=['ENCODING=UTF-8'])

    unique_fields = {}
    for file in matching_files:
        ds = driver.Open(file, 0)
        if ds and ds.GetLayer():
            layer = ds.GetLayer()
            layer_defn = layer.GetLayerDefn()
            for i in range(layer_defn.GetFieldCount()):
                field_defn_shadow = layer_defn.GetFieldDefn(i)
                copied_field_defn = deep_copy_field_defn(field_defn_shadow) #Deep Copy
                unique_fields[copied_field_defn.GetName()] = copied_field_defn #store the copied field defn.
            ds = None # Close the data source after extracting fields
        elif ds:
            ds = None

    for field_defn in unique_fields.values():
        if field_defn and layer_out.CreateField(field_defn) != 0:
            print(f"Error: failed to create field {field_defn.GetName()}")

    # Explicitly set field names.
    layer_defn_out = layer_out.GetLayerDefn()
    for i in range(layer_defn_out.GetFieldCount()):
        original_name = list(unique_fields.keys())[i]
        layer_defn_out.GetFieldDefn(i).SetName(original_name)

    for file in matching_files:
        ds = driver.Open(file, 0)
        if ds and ds.GetLayer():
            layer = ds.GetLayer()
            layer_defn = layer.GetLayerDefn()
            print(f"Processing file: {file} with {layer.GetFeatureCount()} features of geometry type {ogr.GeometryTypeToName(layer_defn.GetGeomType())}")
            layer.ResetReading()
#            for i in range(layer_defn.GetFieldCount()):
#                print({layer_defn.GetFieldDefn(i).GetName()})

            feature = layer.GetNextFeature()
            ErrorCount = 0
            GeomTypeErrCount = 0
            while feature:
                if feature.geometry() and feature.geometry().GetGeometryType() == GeomType:
                    dest_feature = ogr.Feature(layer_defn_out)
                    dest_feature.SetGeometry(feature.GetGeometryRef().Clone())
                    # Copy attributes
                    for i in range(min(layer_defn.GetFieldCount(), layer_defn_out.GetFieldCount())):
                        source_field_defn = layer_defn.GetFieldDefn(i)
                        dest_field_defn = layer_defn_out.GetFieldDefn(layer_defn_out.GetFieldIndex(layer_defn.GetFieldDefn(i).GetName()))
                        if source_field_defn.GetName() == dest_field_defn.GetName() and \
                        source_field_defn.GetType() == dest_field_defn.GetType():
                            dest_feature.SetField(dest_field_defn.GetName(), feature.GetField(source_field_defn.GetName()))
                        else:
                            print(f"Warning: Field mismatch - Source: {source_field_defn.GetName()} ({ogr.GetFieldTypeName(source_field_defn.GetType())}), Destination: {dest_field_defn.GetName()} ({ogr.GetFieldTypeName(dest_field_defn.GetType())})")

                    layer_out.CreateFeature(dest_feature)
                    dest_feature.Destroy()
                else:
                    GeomTypeErrCount = GeomTypeErrCount + 1
                feature = layer.GetNextFeature()
            if ErrorCount > 0:
                print(f"Error: Failed to create {ErrorCount} features from {file}")
            if GeomTypeErrCount > 0:
                print(f"Error: Incorrect Geometry features: {GeomTypeErrCount} from {file}")
            ds = None
        elif ds:
            ds = None

    ds_out = None

def main():
    exclude_not_needed = True
    if "-all" in sys.argv:
        exclude_not_needed = False

    if "-h" in sys.argv:
        print_usage()
        sys.exit(0)

    input_dir = "bdot.shp"

    if not os.path.exists(input_dir) or not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        print_usage()
        sys.exit(1)

    output_area = "area_merged.shp"
    output_line = "line_merged.shp"
    output_point = "point_merged.shp"

    ogr.UseExceptions()

    merge_shapefiles(input_dir, output_line, "_L", ogr.wkbLineString, exclude_not_needed)
#    wait = input("Press Enter to continue.")
    merge_shapefiles(input_dir, output_area, "_A", ogr.wkbPolygon, exclude_not_needed)
#    wait = input("Press Enter to continue.")
    merge_shapefiles(input_dir, output_point, "_P", ogr.wkbPoint, exclude_not_needed)

    print("Merging completed.")

def print_usage():
    print("Usage: python BDOT.shp.exe [-h] [-x]")
    print("Merges shapefiles from 'bdot.shp' directory based on suffixes, merging fields with same name.")
    print("Options:")
    print("  -h: Display this help message.")
    print("  -all: Include files containing '_KUxx', '_ADxx' , '_TCON' & '_SKDR' in processing.")
    print("The script expects a directory named 'bdot.shp' in the current working directory.")
    print("Area shapefiles (with _A suffix) are merged into area_merged.shp.")
    print("Line shapefiles (with _L suffix) are merged into line_merged.shp.")
    print("Point shapefiles (with _P suffix) are merged into point_merged.shp.")

if __name__ == "__main__":
    main()
