using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Outlook = Microsoft.Office.Interop.Outlook;
using System.IO;

namespace ICSOutlookExporter
{
    class Program
    {
        private static void SaveCalendarToDisk()
        {
            string root_project = "gcal_sync";
            //read config file.
            int root_directory_index = Directory.GetCurrentDirectory().ToString().IndexOf(root_project);
            Directory.SetCurrentDirectory(Directory.GetCurrentDirectory().ToString().Substring(0, root_directory_index + root_project.Length));
            string config_path = Path.Combine(Directory.GetCurrentDirectory().ToString(), "sync\\appconfig.py");
            string save_ics_path = Path.Combine(Directory.GetCurrentDirectory().ToString(), "exporters", "data");
            string[] config_text = File.ReadAllLines(config_path);

            bool is_ics_config = false;
            int days_to_sync = 30;
            string output_file = "";

            foreach (string config in config_text)
            {
                if (config == "READER = 'ICS'")
                {
                    is_ics_config = true;
                }

                if (config.Contains("ICS_SYNCH_DAYS"))
                {
                    days_to_sync = Int32.Parse(config.Replace("ICS_SYNCH_DAYS = ", ""));
                }

                if (config.Contains("ICS_DATA_FILENAME"))
                {
                    output_file = config.Replace("ICS_DATA_FILENAME = ", "").Replace("'","");
                }
            }

            if (is_ics_config)
            { 
 
                Outlook.Application oApp = new Outlook.Application();


                Outlook.Folder calendar = oApp.Session.GetDefaultFolder(
                    Outlook.OlDefaultFolders.olFolderCalendar) as Outlook.Folder;
                Outlook.CalendarSharing exporter = calendar.GetCalendarExporter();

                // Set the properties for the export
                exporter.CalendarDetail = Outlook.OlCalendarDetail.olFreeBusyAndSubject;
                exporter.IncludeAttachments = false;
                exporter.IncludePrivateDetails = true;
                exporter.RestrictToWorkingHours = false;
                exporter.IncludeWholeCalendar = false;
                exporter.StartDate = DateTime.Now;
                exporter.EndDate = exporter.StartDate.AddDays(days_to_sync);

                // Save the calendar to disk
                exporter.SaveAsICal(Path.Combine(save_ics_path, output_file));
            }
        }

        static void Main(string[] args)
        {
            SaveCalendarToDisk();
        }
    }
}
