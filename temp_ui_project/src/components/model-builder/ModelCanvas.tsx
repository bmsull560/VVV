import React, { useRef, useEffect, useCallback, useState } from 'react';
import { useDrop } from 'react-dnd';
import { v4 as uuidv4 } from 'uuid';
import { Button } from '../ui/button';
import { ZoomIn, ZoomOut, Maximize, Grid, Link2 as Link, Trash2 } from 'lucide-react';
import * as joint from '@joint/core';
import * as shapes from '@joint/shapes';
import { ModelComponent, CalculationResult } from '../../utils/calculationEngine';
import { ConnectionData } from '../../services/modelBuilderApi';
import styles from './ModelCanvas.module.css';



interface ModelCanvasProps {
  model: {
    components: ModelComponent[];
    connections: ConnectionData[];
  };
  setModel?: (model: { components: ModelComponent[]; connections: ConnectionData[] }) => void;
  onModelChange: (modelData: { components: ModelComponent[]; connections: ConnectionData[]; }) => void;
  calculations: Record<string, CalculationResult>;
  onAddComponent: (component: ModelComponent) => void;
  onDeleteComponent: (componentId: string) => void;
  onSelectComponent: (component: ModelComponent | null) => void;
  selectedComponent: ModelComponent | null;
  getFormattedValue: (value: any, propertyType: string) => string;
  readOnly: boolean;
}

const DEFAULT_COMPONENT_PROPERTIES = {
  'revenue-stream': { amount: 0, growthRate: 0.05 },
  'cost-center': { amount: 0, growthRate: 0.03 },
  'roi-calculator': { period: 3, discountRate: 0.1 },
  'npv-calculator': { discountRate: 0.1 },
  'payback-calculator': { targetPeriod: 12 },
  'sensitivity-analysis': { scenarios: 3 },
  'variable': { value: 0 },
  'formula': { expression: '' }
};

const COMPONENT_COLORS = {
  'revenue-stream': '#10b981',
  'cost-center': '#ef4444',
  'roi-calculator': '#3b82f6',
  'npv-calculator': '#8b5cf6',
  'payback-calculator': '#ec4899',
  'sensitivity-analysis': '#f59e0b',
  'variable': '#6b7280',
  'formula': '#14b8a6'
};

const ModelCanvas: React.FC<ModelCanvasProps> = ({
  model,
  calculations,
  onAddComponent,
  onDeleteComponent,
  onSelectComponent,
  selectedComponent,
  getFormattedValue,
  readOnly
}) => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const paperRef = useRef<joint.dia.Paper | null>(null);
  const graphRef = useRef<joint.dia.Graph | null>(null);
  const [zoom, setZoom] = useState<number>(100);
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);

  // Initialize JointJS graph and paper
  useEffect(() => {
    if (!canvasRef.current) return;

    const graph = new joint.dia.Graph();
    const paper = new joint.dia.Paper({
      el: canvasRef.current,
      model: graph,
      width: '100%',
      height: '100%',
      gridSize: 10,
      drawGrid: true,
      background: {
        color: '#f8fafc'
      },
      defaultConnectionPoint: { name: 'boundary', args: { offset: 10 } },
      defaultRouter: { name: 'manhattan' },
      defaultConnector: { name: 'rounded' },
      interactive: {
        elementMove: !readOnly,
        linkMove: false,

        addLinkFromMagnet: true,


      },
      snapLinks: { radius: 20 },
      linkPinning: false,
      markAvailable: true,
      clickThreshold: 5,
      highlighting: {
        'default': { name: 'stroke', options: { padding: 4 } },
        'connecting': { name: 'stroke', options: { padding: 4, rx: 5, ry: 5 } }
      },
      validateConnection: function(cellViewS, magnetS, cellViewT, magnetT, end, linkView) {
        // Prevent connecting to self
        if (cellViewS === cellViewT) return false;
        
        // Only allow connecting from output to input
        if (magnetS && magnetS.getAttribute('port') === 'in') return false;
        if (magnetT && magnetT.getAttribute('port') === 'out') return false;
        
        return true;
      }
    });

    // Store references
    paperRef.current = paper;
    graphRef.current = graph;

    // Cleanup
    return () => {
      paper.remove();
      graph.clear();
    };
  }, [readOnly]);

  // Handle component selection
  const handleElementClick = useCallback((elementView: joint.dia.ElementView) => {
    const element = elementView.model;
    const componentId = element.get('componentId');
    if (componentId) {
      const component = model.components.find(c => c.id === componentId);
      onSelectComponent(component || null);
    }
  }, [model.components, onSelectComponent]);

  // Handle connection creation
  const handleConnectionCreate = useCallback((linkView: joint.dia.LinkView) => {
    const sourceElement = linkView.model.getSourceElement();
    const targetElement = linkView.model.getTargetElement();
    
    if (sourceElement && targetElement) {
      const sourceId = sourceElement.get('componentId');
      const targetId = targetElement.get('componentId');
      
      if (sourceId && targetId) {
        // Update model with new connection
        console.log(`Connection created from ${sourceId} to ${targetId}`);
        // TODO: Update the model with the new connection
      }
    }
  }, []);

  // Add component to the model and canvas
  const addComponent = useCallback((type: string, position: { x: number; y: number }) => {
    if (!graphRef.current) return;

    const id = uuidv4();
    const component: ModelComponent = {
      id,
      type,
      position,
      properties: { ...(DEFAULT_COMPONENT_PROPERTIES[type as keyof typeof DEFAULT_COMPONENT_PROPERTIES] || {}) }
    };

    // Add to model
    onAddComponent(component);

    // Add to canvas
    const element = new joint.shapes.standard.Rectangle({
      position: { x: position.x, y: position.y },
      size: { width: 120, height: 60 },
      attrs: {
        body: {
          fill: COMPONENT_COLORS[type as keyof typeof COMPONENT_COLORS] || '#6b7280',
          stroke: '#000',
          strokeWidth: 1,
          rx: 4,
          ry: 4
        },
        label: {
          text: type,
          fill: '#fff',
          fontSize: 12,
          fontWeight: 'bold',
          textWrap: {
            width: 100,
            height: 50,
            ellipsis: true
          }
        }
      },
      componentId: id,
      componentType: type
    });

    graphRef.current.addCell(element);
    onSelectComponent(component);
  }, [onAddComponent, onSelectComponent]);

  // Handle drop from component library
  const [{ isOver }, drop] = useDrop<{ componentType: string }, void, { isOver: boolean }>({
    accept: 'MODEL_COMPONENT',
    drop: (item, monitor) => {
      if (!monitor.isOver() || !canvasRef.current) return;

      const clientOffset = monitor.getClientOffset();
      if (!clientOffset) return;

      const canvasRect = canvasRef.current.getBoundingClientRect();
      const x = clientOffset.x - canvasRect.left;
      const y = clientOffset.y - canvasRect.top;

      addComponent(item.componentType, { x, y });
    },
    collect: (monitor) => ({
      isOver: monitor.isOver()
    })
  });

  // Zoom functions
  const zoomIn = useCallback(() => {
    if (!paperRef.current) return;
    const currentScale = paperRef.current.scale().sx;
    paperRef.current.scale(currentScale * 1.2);
    setZoom(Math.round(currentScale * 1.2 * 100));
  }, []);

  const zoomOut = useCallback(() => {
    if (!paperRef.current) return;
    const currentScale = paperRef.current.scale().sx;
    paperRef.current.scale(currentScale / 1.2);
    setZoom(Math.round((currentScale / 1.2) * 100));
  }, []);

  const fitToWindow = useCallback(() => {
    if (!paperRef.current) return;
    paperRef.current.scaleContentToFit({ padding: 20 });
    setZoom(100);
  }, []);

  // Toggle grid visibility
  const toggleGrid = useCallback(() => {
    if (!paperRef.current) return;
    const newShowGrid = !showGrid;
    setShowGrid(newShowGrid);
    paperRef.current.drawGrid({
      name: newShowGrid ? 'dot' : 'none',
      args: { color: '#e2e8f0', thickness: 1 }
    });
  }, [showGrid]);

  // Delete selected component
  const deleteSelected = useCallback(() => {
    if (!selectedComponent || !graphRef.current) return;
    
    // Remove from canvas
    const elements = graphRef.current.getElements();
    const elementToRemove = elements.find(el => el.get('componentId') === selectedComponent.id);
    if (elementToRemove) {
      elementToRemove.remove();
    }
    
    // Remove from model
    onDeleteComponent(selectedComponent.id);
    onSelectComponent(null);
  }, [selectedComponent, onDeleteComponent, onSelectComponent]);

  // Set up event listeners
  useEffect(() => {
    const paper = paperRef.current;
    if (!paper) return;

    paper.on('element:pointerclick', handleElementClick);
    paper.on('link:add', handleConnectionCreate);

    return () => {
      paper.off('element:pointerclick', handleElementClick);
      paper.off('link:add', handleConnectionCreate);
    };
  }, [handleElementClick, handleConnectionCreate]);



  return (
    <div className={styles.modelCanvasContainer}>
      <div className={styles.toolbar}>
        <div className={styles.zoomControls}>
          <Button variant="outline" size="sm" onClick={zoomIn} aria-label="Zoom In">
            <ZoomIn size={16} />
          </Button>
          <Button variant="outline" size="sm" onClick={zoomOut} aria-label="Zoom Out">
            <ZoomOut size={16} />
          </Button>
          <Button variant="outline" size="sm" onClick={fitToWindow} aria-label="Fit to Content">
            <Maximize size={16} />
          </Button>
          <Button 
            variant={showGrid ? 'default' : 'outline'} 
            size="sm" 
            onClick={toggleGrid} 
            aria-label="Toggle Grid"
          >
            <Grid size={16} />
          </Button>
          <Button 
            variant={isConnecting ? 'default' : 'outline'} 
            size="sm" 
            onClick={() => setIsConnecting(!isConnecting)}
            aria-label={isConnecting ? 'Cancel Connection' : 'Connect Components'}
          >
            <Link size={16} />
          </Button>
          <Button 
            variant="destructive" 
            size="sm" 
            onClick={deleteSelected} 
            disabled={!selectedComponent}
            aria-label="Delete Selected"
          >
            <Trash2 size={16} />
          </Button>
        </div>
        <div className={styles.zoomLevel}>{zoom}%</div>
      </div>
      
      <div 
        ref={(node: HTMLDivElement) => {
          (canvasRef as React.MutableRefObject<HTMLDivElement | null>).current = node;
          drop(node);
        }}
        className={`${styles.canvas} ${isOver ? styles.canvasHover : ''}`}
      />
    </div>
  );
};

export default ModelCanvas;
