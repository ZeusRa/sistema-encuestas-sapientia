import { Paper, InputBase, IconButton, Divider, Box, Chip } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';

const OdooSearchBar = () => {
  return (
    <Paper
      component="form"
      sx={{ p: '2px 4px', display: 'flex', alignItems: 'center', width: 400, height: 40, bgcolor: 'background.paper', border: '1px solid #e0e0e0' }}
      elevation={0}
    >
      <IconButton sx={{ p: '10px' }} aria-label="search">
        <SearchIcon />
      </IconButton>
      
      <InputBase
        sx={{ ml: 1, flex: 1, fontSize: '0.9rem' }}
        placeholder="Buscar..."
        inputProps={{ 'aria-label': 'buscar encuestas' }}
      />
      
      <Divider sx={{ height: 28, m: 0.5 }} orientation="vertical" />
      
      <IconButton color="primary" sx={{ p: '10px' }} aria-label="filtros">
        <ArrowDropDownIcon />
      </IconButton>
    </Paper>
  );
};

export default OdooSearchBar;