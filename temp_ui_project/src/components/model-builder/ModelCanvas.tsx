import React, { useRef, useEffect, useCallback, useState } from 'react';
import { useDrop } from 'react-dnd';
import { v4 as uuidv4 } from 'uuid';
import { Button } from '../ui/button';
import { ZoomIn, ZoomOut, Maximize, Grid, Link2 as Link, Trash2 } from 'lucide-react';
import * as joint from '@joint/core';
import type { ModelComponent } from '../../utils/calculationEngine';
import type { ConnectionData } from '../../services/modelBuilderApi';
import styles from './ModelCanvas.module.css';

interface ModelCanvasProps {
  model: {
    components: ModelComponent[];
    connections: ConnectionData[];
  };
  setModel?: (model: { components: ModelComponent[]; connections: ConnectionData[] }) => void;
  onModelChange: (modelData: { components: ModelComponent[]; connections: ConnectionData[] }) => void;
  onAddComponent: (component: ModelComponent) => void;
  onDeleteComponent: (componentId: string) => void;
  onSelectComponent: (component: ModelComponent | null) => void;
  selectedComponent: ModelComponent | null;
  readOnly: boolean;
  className?: string;
}

// Consider moving these to a shared constants file if used elsewhere
const DEFAULT_COMPONENT_PROPERTIES = {
  'revenue-stream': { unitPrice: 0, quantity: 0, growthRate: 0.05, periods: 12 },
  'cost-center': { monthlyCost: 0, periods: 12, escalationRate: 0.03 },
  'roi-calculator': { investment: 0, annualBenefit: 0, periods: 12 },
  'npv-calculator': { cashFlows: [0] as number[], discountRate: 0.1 },
  'payback-calculator': { investment: 0, annualBenefit: 0 },
  'sensitivity-analysis': { baseValue: 0, rangeMin: 0, rangeMax: 0, variableName: '' },
  'variable': { value: 0 },
  'formula': { expression: '', variables: {} }
} as const;

const COMPONENT_COLORS: Record<string, string> = {
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

  onAddComponent,
  onDeleteComponent,
  onSelectComponent,
  selectedComponent,

  readOnly
}) => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const paperRef = useRef<joint.dia.Paper | null>(null);
  const graphRef = useRef<joint.dia.Graph | null>(null);
  const [zoom, setZoom] = useState<number>(100);
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);

  useEffect(() => {
    if (!canvasRef.current) return;

    const graph = new joint.dia.Graph({}, { cellNamespace: joint.shapes });
    const paper = new joint.dia.Paper({
      el: canvasRef.current,
      model: graph,
      width: '100%',
      height: '100%',
      gridSize: 10,
      drawGrid: true,
      background: {
        color: '#f8f8f8',
      },
      linkPinning: false,
      snapLinks: true,
      embedding: true,
      validateConnection: (
  cellViewS: joint.dia.CellView,
  magnetS: SVGElement,
  cellViewT: joint.dia.CellView,
  magnetT: SVGElement
) => {
        if (cellViewS === cellViewT) return false;

        if (magnetS && magnetS.getAttribute('port-group') === 'in' && magnetT && magnetT.getAttribute('port-group') === 'in') return false;
        if (magnetS && magnetS.getAttribute('port-group') === 'out' && magnetT && magnetT.getAttribute('port-group') === 'out') return false;

        if (magnetS && magnetS.getAttribute('port-group') === 'in') return false;
        if (magnetT && magnetT.getAttribute('port-group') === 'out') return false;

        return true;
      },
      defaultLink: new joint.dia.Link({
        attrs: {
          line: {
            stroke: '#8f8f8f',
            strokeWidth: 3,
            targetMarker: { 'type': 'path', 'd': 'M 10 -5 0 0 10 5 Z' }
          }
        }
      }),
      interactive: { linkMove: false, elementMove: !readOnly }
    });

    paperRef.current = paper;
    graphRef.current = graph;

    return () => {
      paper.scale(1, 1);
      graph.clear();
    };
  }, [readOnly]);

  const handleElementClick = useCallback((elementView: joint.dia.ElementView) => {
    const element = elementView.model;
    const componentId = element.get('componentId');
    if (componentId) {
      const component = model.components.find(c => c.id === componentId);
      onSelectComponent(component || null);
    }
  }, [model.components, onSelectComponent]);

  const handleConnectionCreate = useCallback((linkView: joint.dia.LinkView) => {
    const sourceElement = linkView.model.getSourceElement();
    const targetElement = linkView.model.getTargetElement();
    
    if (sourceElement && targetElement) {
      const sourceId = sourceElement.get('componentId');
      const targetId = targetElement.get('componentId');
      
      if (sourceId && targetId) {
        console.log(`Connection created from ${sourceId} to ${targetId}`);
      }
    }
  }, []);

  const addComponent = useCallback((type: string, position: { x: number; y: number }) => {
    if (!graphRef.current) return;

    const id = uuidv4();
    const component: ModelComponent = {
      id,
      type,
      position,
      properties: { ...(DEFAULT_COMPONENT_PROPERTIES[type as keyof typeof DEFAULT_COMPONENT_PROPERTIES] || {}) }
    };

    onAddComponent(component);

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

  const zoomIn = useCallback(() => {
    if (!paperRef.current) return;
    const currentScale = paperRef.current.scale().sx;
    paperRef.current.scale(currentScale * 1.2, currentScale * 1.2);
    setZoom(Math.round(currentScale * 1.2 * 100));
  }, []);

  const zoomOut = useCallback(() => {
    if (!paperRef.current) return;
    const currentScale = paperRef.current.scale().sx;
    paperRef.current.scale(currentScale / 1.2, currentScale / 1.2);
    setZoom(Math.round((currentScale / 1.2) * 100));
  }, []);

  const fitToWindow = useCallback(() => {
    if (!paperRef.current) return;
    paperRef.current.scaleContentToFit({ padding: 20 });
    setZoom(100);
  }, []);

  const toggleGrid = useCallback(() => {
    if (!paperRef.current) return;
    const newShowGrid = !showGrid;
    setShowGrid(newShowGrid);
    paperRef.current.drawGrid({
      name: newShowGrid ? 'dot' : 'none',
      args: { color: '#e2e8f0', thickness: 1 }
    });
  }, [showGrid]);

  const deleteSelected = useCallback(() => {
    if (!selectedComponent || !graphRef.current) return;
    
    const elements = graphRef.current.getElements();
    const elementToRemove = elements.find((el: joint.dia.Element) => el.get('componentId') === selectedComponent.id);
    if (elementToRemove) {
      graphRef.current.removeCells([elementToRemove]);
    }
    
    onDeleteComponent(selectedComponent.id);
    onSelectComponent(null);
  }, [selectedComponent, onDeleteComponent, onSelectComponent]);

  useEffect(() => {
    const paper = paperRef.current;
    if (!paper) return;

    paper.on('element:pointerdblclick', handleElementClick);
    paper.on('link:pointerdblclick', handleConnectionCreate);
    paper.on('blank:pointerdown', () => {});

    return () => {
      paper.off('element:pointerdblclick');
      paper.off('link:pointerdblclick');
      paper.off('blank:pointerdown');
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
