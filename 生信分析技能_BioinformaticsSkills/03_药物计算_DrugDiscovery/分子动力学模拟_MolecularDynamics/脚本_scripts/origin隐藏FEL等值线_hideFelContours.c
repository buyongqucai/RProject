#include <origin.h>
#pragma labtalk(1)

void hide_fel_contours()
{
    GraphLayer gl = Project.ActiveLayer();
    int n = gl.DataPlots.Count();
    for (int i = 0; i < n; i++)
    {
        DataPlot dp = gl.DataPlots(i);
        if (!dp.IsValid())
            continue;

        Tree tr;
        if (dp.GetColormap(tr))
        {
            vector<int> vLShow;
            vLShow = tr.Details.ShowLines.nVals;
            vLShow = 0;
            tr.Details.Remove();
            tr.Details.ShowLines.nVals = vLShow;
            dp.SetColormap(tr);
        }

        Tree trf;
        trf = dp.GetFormat(FPB_ALL, FOB_ALL, true, true);
        if (trf.Root.Surface.Mesh.Enable)
            trf.Root.Surface.Mesh.Enable.nVal = 0;
        if (trf.Root.Surface.ColorMap.Contours.Enable)
            trf.Root.Surface.ColorMap.Contours.Enable.nVal = 0;
        if (trf.Root.ColorMap.Contours.Enable)
            trf.Root.ColorMap.Contours.Enable.nVal = 0;
        if (trf.Root.ColorMap.ShowGridLines)
            trf.Root.ColorMap.ShowGridLines.nVal = 0;
        if (trf.Root.Grids.Enable)
            trf.Root.Grids.Enable.nVal = 0;
        dp.UpdateThemeIDs(trf.Root);
        dp.ApplyFormat(trf, true, true);
    }
}
