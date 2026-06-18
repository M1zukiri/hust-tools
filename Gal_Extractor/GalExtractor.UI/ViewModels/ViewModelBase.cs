
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace GalExtractor.UI.ViewModels
{
    /// <summary>
    /// Base class for ViewModels that implements INotifyPropertyChanged
    /// </summary>
    public abstract class ViewModelBase : INotifyPropertyChanged
    {
        public event PropertyChangedEventHandler? PropertyChanged;

        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
